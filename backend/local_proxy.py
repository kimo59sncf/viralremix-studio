#!/usr/bin/env python3
"""Proxy HTTP local qui relaie vers le proxy d'entreprise avec SSO (SSPI).

Le proxy SNCF (Cisco WSA) accepte l'authentification préemptive Negotiate/Kerberos
(SPN = HTTP/<proxy>). Ce petit relais local permet à pip / npm de l'utiliser,
car ils ne savent pas faire d'authentification Windows (NTLM/Kerberos).
"""
import base64
import socket
import threading

import sspi  # fourni par pywin32

UPSTREAM_HOSTS = ["web-pa-7.access.sncf.fr", "web-pa-12.access.sncf.fr"]
UPSTREAM_PORT = 8080
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8899
TIMEOUT = 90


def _token_bytes(res):
    err, desc = res
    if desc is not None and len(desc):
        return err, desc[0].Buffer
    return err, b""


def _read_head(sock, initial=b""):
    buf = initial
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
    head, _, rest = buf.partition(b"\r\n\r\n")
    return head, rest


def _header(head, name):
    for line in head.split(b"\r\n"):
        if line.lower().startswith(name.lower() + b":"):
            return line.split(b":", 1)[1].strip()
    return b""


def _parse_proxy_auth(head):
    offers = []
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"proxy-authenticate:"):
            value = line.split(b":", 1)[1].strip()
            parts = value.split(None, 1)
            scheme = parts[0].decode(errors="replace")
            token = b""
            if len(parts) > 1:
                try:
                    token = base64.b64decode(parts[1].strip())
                except Exception:
                    token = b""
            offers.append((scheme, token))
    for pref in ("Negotiate", "NTLM"):
        for scheme, token in offers:
            if scheme.lower() == pref.lower():
                return pref, token
    if offers:
        return offers[0][0], offers[0][1]
    return "NTLM", b""


def _connect_upstream(host):
    s = socket.create_connection((host, UPSTREAM_PORT), timeout=TIMEOUT)
    s.settimeout(TIMEOUT)
    return s


def _connect_request(host, port, auth_header=""):
    return (
        f"CONNECT {host}:{port} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Proxy-Connection: keep-alive\r\n"
        f"{auth_header}"
        "\r\n"
    ).encode()


def _make_auth(proxy_host):
    """Crée un contexte SSPI Negotiate pour le proxy donné et renvoie (auth, token)."""
    auth = sspi.ClientAuth("Negotiate", targetspn=f"HTTP/{proxy_host}")
    _, token = _token_bytes(auth.authorize(None))
    return auth, token or b""


def establish_tunnel(host, port):
    last_err = None
    for proxy_host in UPSTREAM_HOSTS:
        s = None
        try:
            s = _connect_upstream(proxy_host)
            auth, token = _make_auth(proxy_host)
            auth_scheme = "Negotiate"

            for _ in range(3):
                hdr = f"Proxy-Authorization: {auth_scheme} {base64.b64encode(token).decode()}\r\n"
                s.sendall(_connect_request(host, port, auth_header=hdr))
                head, leftover = _read_head(s)
                status = head.split(b"\r\n", 1)[0]
                if b" 200" in status:
                    return s, leftover
                if b" 407" not in status:
                    raise RuntimeError(f"CONNECT refusé : {status.decode(errors='replace')}")

                auth_scheme, challenge = _parse_proxy_auth(head)
                if not challenge:
                    raise RuntimeError("Le proxy n'a pas fourni de challenge d'authentification.")

                _, token = _token_bytes(auth.authorize(challenge))
                token = token or b""

                if _header(head, b"connection").lower() == b"close":
                    s.close()
                    s = _connect_upstream(proxy_host)

            raise RuntimeError("Authentification proxy : trop de tours négociés.")
        except Exception as e:
            last_err = e
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
            continue
    raise RuntimeError(f"Impossible d'établir le tunnel : {last_err}")


def _pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(client):
    upstream = None
    try:
        head, leftover = _read_head(client)
        if not head:
            client.close()
            return
        parts = head.split(b"\r\n", 1)[0].split()
        if len(parts) < 2:
            client.close()
            return
        method = parts[0].upper()

        if method == b"CONNECT":
            target = parts[1].decode(errors="replace")
            host, _, port_s = target.partition(":")
            port = int(port_s) if port_s else 443
            upstream, up_leftover = establish_tunnel(host, port)
            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            if up_leftover:
                client.sendall(up_leftover)
            threading.Thread(target=_pipe, args=(client, upstream), daemon=True).start()
            _pipe(upstream, client)
        else:
            _forward_http(client, head, leftover)
    except Exception:
        try:
            client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
        except OSError:
            pass
    finally:
        try:
            client.close()
        except OSError:
            pass
        if upstream is not None:
            try:
                upstream.close()
            except OSError:
                pass


def _forward_http(client, head, leftover):
    body = leftover
    clen = 0
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            try:
                clen = int(line.split(b":", 1)[1].strip() or 0)
            except ValueError:
                clen = 0
    while len(body) < clen:
        chunk = client.recv(65536)
        if not chunk:
            break
        body += chunk

    for proxy_host in UPSTREAM_HOSTS:
        s = None
        try:
            s = _connect_upstream(proxy_host)
            auth, token = _make_auth(proxy_host)
            auth_scheme = "Negotiate"

            for _ in range(3):
                lines = head.split(b"\r\n")
                merged = [lines[0]]
                merged.append(f"Proxy-Authorization: {auth_scheme} {base64.b64encode(token).decode()}")
                merged.extend(lines[1:])
                s.sendall(b"\r\n".join(merged) + b"\r\n\r\n")
                if body:
                    s.sendall(body)

                resp, rest = _read_head(s)
                status = resp.split(b"\r\n", 1)[0]
                if b" 407" not in status:
                    client.sendall(resp + b"\r\n\r\n" + rest)
                    while True:
                        data = s.recv(65536)
                        if not data:
                            break
                        client.sendall(data)
                    s.close()
                    return

                auth_scheme, challenge = _parse_proxy_auth(resp)
                if not challenge:
                    raise RuntimeError("Pas de challenge d'authentification.")
                _, token = _token_bytes(auth.authorize(challenge))
                token = token or b""
                if _header(resp, b"connection").lower() == b"close":
                    s.close()
                    s = _connect_upstream(proxy_host)

            raise RuntimeError("Authentification HTTP échouée.")
        except Exception:
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass

    try:
        client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
    except OSError:
        pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((LISTEN_HOST, LISTEN_PORT))
    srv.listen(128)
    print(f"[proxy] {LISTEN_HOST}:{LISTEN_PORT} -> {', '.join(UPSTREAM_HOSTS)}:{UPSTREAM_PORT}")
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()



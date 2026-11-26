#!/usr/bin/env python3
"""NTP-сервер со сдвигом для Aqara Camera E1.

Обновлено: 2026-11-26

Камера CH-C01E получает UTC по NTP, но OSD рисует с поясом UTC+2
(вместо Москвы UTC+3) → ровно −1 час. Отдаём «UTC» на час вперёд,
чтобы OSD совпал с Europe/Moscow, не ломая chrony для остальной сети.

Слушает только BIND_ADDR (вторичный IP Pi3).
"""
from __future__ import annotations

import argparse
import socket
import struct
import time

NTP_DELTA = 2208988800  # 1970↔1900
SKEW_SEC = 3600  # +1 час


def ntp_ts(now: float) -> bytes:
    sec = int(now) + NTP_DELTA
    frac = int((now % 1.0) * (1 << 32)) & 0xFFFFFFFF
    return struct.pack("!II", sec, frac)


def build_reply(req: bytes, now: float) -> bytes:
    """Минимальный NTP response (LI=0, VN=from req, mode=4 server)."""
    if len(req) < 48:
        req = req.ljust(48, b"\0")
    vn = (req[0] >> 3) & 0x07
    if vn < 1 or vn > 4:
        vn = 3
    first = (0 << 6) | (vn << 3) | 4  # LI=0, mode=server
    header = struct.pack(
        "!BBbbIII",
        first,
        2,  # stratum
        req[2],  # poll
        -20,  # precision
        0,  # root delay
        0,  # root dispersion
        0x4C4F434C,  # refid 'LOCL'
    )
    ref = ntp_ts(now)
    originate = req[40:48]
    recv = ntp_ts(now)
    xmit = ntp_ts(now)
    return header + ref + originate + recv + xmit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bind", default="10.0.20.48")
    ap.add_argument("--port", type=int, default=123)
    ap.add_argument("--skew", type=int, default=SKEW_SEC)
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.bind, args.port))
    print(
        f"aqara-ntp-skew listening on {args.bind}:{args.port} skew=+{args.skew}s",
        flush=True,
    )
    while True:
        data, addr = sock.recvfrom(128)
        now = time.time() + args.skew
        try:
            sock.sendto(build_reply(data, now), addr)
        except OSError as exc:
            print(f"send fail {addr}: {exc}", flush=True)


if __name__ == "__main__":
    main()

# Aqara Camera E1 (CH-C01E) — синхронизация времени

**Обновлено:** 2026-11-26

## Устройство
- mDNS: `Camera-E1-E147`
- Модель: **CH-C01E**
- MAC: `54:EF:44:5A:E1:47`
- DHCP reservation: **10.0.20.9** (после renew; до renew может быть другой IP)
- HAP `:40271`, RTSP `:8554` (нужен пароль из Aqara Home)

## Причина
`ntp.aqara.com` / `time.aqara.com` резолвятся в **китайский** `120.53.71.194`.  
С гаража **UDP/123** до этого адреса **не отвечает** (TCP/443 при этом ок).  
Камера не получает NTP → OSD-время уезжает.

## Исправление (Pi3 + Time Capsule)
1. **chrony** на Pi3 (`10.0.20.56`) — NTP-сервер для LAN (`allow 10.0.20.0/24`).
2. **dnsmasq** на Pi3 — `ntp.aqara.com` / `time.aqara.com` / `ntp.aliyun.com` → `10.0.20.56`.
3. **UFW** — разрешены UDP/TCP 53 и UDP 123 с `10.0.20.0/24`.
4. **Time Capsule dnscache** — файлы  
   `/var/sv/dnscache/root/servers/{ntp.aqara.com,time.aqara.com,ntp.aliyun.com,ntp1.aliyun.com}`  
   содержат `10.0.20.56` (точечный forward, без поломки общего DNS).
5. **DHCP** на капсуле: `option domain-name-servers 10.0.20.56, 10.0.20.1;`  
   `option ntp-servers 10.0.20.56;` + резерв MAC→IP.
6. Persist: `/mnt/Flash/apply-aqara-ntp-dns.sh` + `dhcpd.conf.desired` в `rc.local`.

## Проверка
```bash
# DNS через капсулу
python3 -c "..."  # ntp.aqara.com @10.0.20.1 → 10.0.20.56
# NTP
chronyc tracking
# с LAN
echo | nc -u -w2 10.0.20.56 123
```

## Aqara Home
Дополнительно в приложении: **Дом → Настройки дома → Время / часовой пояс** = Москва (Europe/Moscow).  
Это влияет на отображаемый локальный пояс поверх NTP.

## После фикса
Если OSD ещё старое — один раз выключить/включить питание камеры (форс NTP).  
SSH на капсулу: `ssh tc` (включается через ACP при необходимости).

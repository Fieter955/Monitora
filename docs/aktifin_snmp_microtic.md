# 1. Menghidupkan fitur SNMP di MikroTik
/snmp set enabled=yes contact="Admin BTP" location="Balai Teknik Pantai"

# 2. Membuat password community 'public_v2' (Hanya-baca & khusus IP laptop/server 192.168.30.236)
/snmp community add name=mikrotik_monitora addresses=192.168.30.236/32 read-access=yes

# 3. Membuka izin firewall port UDP 161 khusus untuk laptop/server Monitora
/ip firewall filter add chain=input protocol=udp dst-port=161 src-address=192.168.30.236 action=accept comment="Allow SNMP from Monitora" place-before=1
import json, pathlib
dashboards = {
    'infrastructure-overview.json': 'Ringkasan',
    'servers-linux.json': 'Server Linux',
    'servers-windows.json': 'Server Windows',
    'network-devices.json': 'Perangkat Jaringan'
}
folder = pathlib.Path('infra/grafana/dashboards')

base_links = [
  {'icon': 'dashboard', 'tags': [], 'targetBlank': False, 'title': 'Ringkasan', 'tooltip': '', 'type': 'link', 'url': '/d/infrastructure-overview?kiosk'},
  {'icon': 'external link', 'tags': [], 'targetBlank': False, 'title': 'Server Linux', 'tooltip': '', 'type': 'link', 'url': '/d/servers-linux?kiosk'},
  {'icon': 'external link', 'tags': [], 'targetBlank': False, 'title': 'Server Windows', 'tooltip': '', 'type': 'link', 'url': '/d/servers-windows?kiosk'},
  {'icon': 'external link', 'tags': [], 'targetBlank': False, 'title': 'Perangkat Jaringan', 'tooltip': '', 'type': 'link', 'url': '/d/network-devices?kiosk'}
]

for filename, active_title in dashboards.items():
    p = folder / filename
    if p.exists():
        data = json.loads(p.read_text(encoding='utf-8'))
        
        new_links = []
        for link in base_links:
            l = link.copy()
            if l['title'] == active_title:
                l['title'] = '🟢 ' + l['title']
                l['icon'] = 'dashboard'
            else:
                l['icon'] = 'doc'
            new_links.append(l)
            
        data['links'] = new_links
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Updated ' + filename)

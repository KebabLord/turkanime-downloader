import json
import os

class Dosyalar:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.main_dir = os.path.abspath(os.path.join(self.base_dir, '..'))
        self.gecmis_path = os.path.join(self.main_dir, 'gecmis.json')

        if not os.path.exists(self.gecmis_path):
            self.gecmis = {"izlendi": {}, "indirildi": {}}
            self.save_gecmis()
        else:
            self.load_gecmis()

    def load_gecmis(self):
        try:
            with open(self.gecmis_path, 'r', encoding='utf-8') as f:
                self.gecmis = json.load(f)
        except json.JSONDecodeError:
            self.gecmis = {"izlendi": {}, "indirildi": {}}
            self.save_gecmis()

    def save_gecmis(self):
        with open(self.gecmis_path, 'w', encoding='utf-8') as f:
            json.dump(self.gecmis, f, ensure_ascii=False, indent=4)

    def set_gecmis(self, anime_slug, bolum_slug, mark_type):
        if mark_type not in self.gecmis:
            self.gecmis[mark_type] = {}
        if anime_slug not in self.gecmis[mark_type]:
            self.gecmis[mark_type][anime_slug] = []
        if bolum_slug not in self.gecmis[mark_type][anime_slug]:
            self.gecmis[mark_type][anime_slug].append(bolum_slug)
            self.save_gecmis()

    def get_gecmis(self, anime_slug, mark_type):
        return self.gecmis.get(mark_type, {}).get(anime_slug, [])

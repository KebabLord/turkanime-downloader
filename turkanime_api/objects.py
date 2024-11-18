""" Örnek:
>>> ani = Anime(driver,"non-non-biyori")
>>> bol3 = ani.bolumler[2]
>>> vid1 = bol3.videos[0]
>>> vid1.oynat()
"""
from os import remove
from os.path import join
from tempfile import NamedTemporaryFile
import subprocess as sp
import re
import json
import yt_dlp
import requests
from .bypass import get_real_url

# Çalıştığı bilinen playerlar ve öncelikleri
SUPPORTED = [
    "GDRIVE",
    "GPLUS",
    "MP4UPLOAD",
    "YADISK",
    "MAIL",
    "ODNOKLASSNIKI",
    "VK",
    "DAILYMOTION",
    "SIBNET",
    "VIDMOLY",
    "YOURUPLOAD",
    "SENDVID",
    "MYVI",
    "UQLOAD",
]

class LogHandler:
    """ TODO: ytdlp log handler prototipi """
    @staticmethod
    def error(msg):
        pass
    @staticmethod
    def warning(msg):
        pass
    @staticmethod
    def debug(msg):
        pass


class Anime:
    """
    Bir anime serisi hakkında her verinin bulunduğu obje.
    Obje'yi yaratmak için animenin kodu veya URL'si yeterlidir.

    Öznitelikler:
    - slug: Animenin kodu: "non-non-biyori".
    - title: Animenin okunaklı ismi, örneğin: Non Non Biyori
    - anime_id: Animenin türkanime id'si. Bölümleri ve anime resmini getirirken gerekli.
    - bolumler_data: Anime bölümlerinin [(slug:str,isim:str),] formatında listesi.
    - bolumler: Anime bölümlerinin [bolum1:Bolum,bolum2:Bolum,] formatında obje listesi.
    - info: Anime sayfasından parse'lanan özet,kategori,stüdyo gibi meta bilgileri içeren dict.
    - parse_fansubs: Bolum objesi yaratılırken fansubları da parse'lamasını belirt.
    """
    def __init__(self,driver,slug,parse_fansubs=True):
        self.driver = driver
        self.slug = slug
        self.title = None
        self.anime_id = 0
        self.info = {
            "Kategori":None,
            "Japonca":None,
            "Anime Türü":[],
            "Bölüm Sayısı":0,
            "Başlama Tarihi":None,
            "Bitiş Tarihi":None,
            "Stüdyo":None,
            "Puanı":0.0,
            "Özet":None,
            "Resim":None
        }
        self.fetch_info()
        self._bolumler_data = None
        self._bolumler = []
        self.parse_fansubs = parse_fansubs

    def fetch_info(self):
        """Anime detay sayfasını ayrıştır."""
        script = f"""
        var callback = arguments[arguments.length - 1];
        fetch('/anime/{self.slug}')
            .then(response => response.text())
        .then(data => {{
            callback(data);
        }})
        .catch(error => {{
            callback(null);
        }});
    """
    src = self.driver.execute_async_script(script)
    if src is None:
        raise Exception("Failed to fetch anime info.")
    self._parse_info(src)


        # Anime sayfasındaki bilgi tablosunu parse'la
        info_table=re.findall(r'<div id="animedetay">(<table.*?</table>)',src)[0]
        raw_m = re.findall(r"<tr>.*?<b>(.*?)<\/b>.*?width.*?>(.*?)<\/td>.*?<\/tr>",info_table)
        for key,val in raw_m:
            if not key in self.info:
                continue
            val = re.sub("<.*?>","",val)
            val = re.sub("^ {1,3}","",val)
            if key == "Puanı":
                val = float(re.findall("^(.*?) ",val).pop())
            elif key == "Anime Türü":
                val = val.split("  ")
            self.info[key] = val
        self.info["Özet"] = re.findall('"ozet">(.*?)</p>',info_table)[0]

    def get_bolum_listesi(self):
        """ Anime bölümlerinin [(slug,isim),] formatında listesi. """
        anime_id = self.anime_id
        src = self.driver.execute_script(f"return $.get('/ajax/bolumler&animeId={anime_id}')")
        return re.findall(r'\/video\/(.*?)\\?".*?title=.*?"(.*?)\\?"',src)

    @staticmethod
    def get_anime_listesi(driver):
        """ Anime serilerinin [(slug,isim),] formatında listesi. """
        src = driver.execute_script("return $.get('/ajax/tamliste')")
        return re.findall(r'\/anime\/(.*?)".*?animeAdi">(.*?)<',src)

    @property
    def bolumler(self):
        """ Anime bölümlerinin [Bolum,] formatında listesi. """
        if not self._bolumler:
            for slug,title in self.get_bolum_listesi():
                self._bolumler.append(
                    Bolum(
                        self.driver,
                        slug=slug,
                        title=title,
                        anime=self,
                        parse_fansubs=self.parse_fansubs))
        return self._bolumler



class Bolum:
    """
    Bir anime bölum'ünü temsil eden obje.
    Obje'yi yaratmak için bölümün kodu veya URL'si yeterlidir.

    Öznitelikler:
    - slug: Bölümün kodu: "naruto-54-bolum" veya URLsi: "https://turkani.co/video/naruto-54-bolum".
    - title: Bölümün okunaklı ismi. (opsiyonel)
    - anime: Bölümün ait olduğu anime'nin objesi, eğer tanımlanmadıysa erişildiğinde yaratılır.
    - parse_fansubs: Fansubları da parse'la. Fazladan fansub sayısı kadar istek gönderir.
    """
    def __init__(self,driver,slug,anime=None,title=None,parse_fansubs=True):
        if "http" == slug[:4]:
            slug = slug.split("/")[-1]
        self.driver = driver
        self.slug = slug
        self.parse_fansubs = parse_fansubs
        self._title = title
        self._html = None
        self._videos = []
        self._anime = anime
        self._fansubs = []

    @property
    def html(self):
        if self._html is None:
            self._html = self.driver.execute_script(f'return $.get("/video/{self.slug}")')
        return self._html

    @property
    def title(self):
        if self._title is None:
            self._title = re.findall(r'<title>(.*?)<\/title>',self.html)[0]
        return self._title

    @property
    def videos(self):
        if not self._videos:
            self.get_videos()
        return self._videos

    @property
    def anime(self):
        """ Bu bölümün ait olduğu anime serisi objesini yarat. """
        if self._anime is None:
            ...
        return self._anime

    @property
    def fansubs(self):
        """ Bölüm sayfasından fansub listesini ayrıştır. """
        if not self._fansubs:
            self._fansubs = re.findall(r"</span> ([^<>/]*?)</a></button>",self.html)
            if not self._fansubs:
                self._fansubs = re.findall(r"</span> ([^\\<>]*)</button>.*?iframe",self.html)
        return self._fansubs

    def get_videos(self):
        self._videos = []
        # Yalnızca tek bir fansub varsa
        if not re.search(".*birden fazla grup",self.html):
            fansub = re.findall(r"</span> ([^\\<>]*)</button>.*?iframe",self.html)[0]
            vids=re.findall(r"(ajax\/videosec&b=[A-Za-z0-9]+&v=.*?)'.*?<\/span> ?(.*?)<\/button",self.html)
            for vpath,player in vids:
                self._videos.append(Video(self,vpath,player,fansub))
        # Fansublar da parse'lanacaksa
        elif self.parse_fansubs:
            fansubs = re.findall(r"(ajax\/videosec&.*?)'.*?<\/span> ?(.*?)<\/a>",self.html)
            for path,fansub in fansubs:
                src = self.driver.execute_script(f'return $.get("{path}")')
                vids=re.findall(r"(ajax\/videosec&b=[A-Za-z0-9]+&v=.*?)'.*?<\/span> ?(.*?)<\/button",src)
                for vpath,player in vids:
                    self._videos.append(Video(self,vpath,player,fansub))
        # Fansubları parselamaksızın tüm videoları getir
        else:
            allpath = re.findall(r"(ajax\/videosec&b=[A-Za-z0-9]+.*?)&[fv]=.*?'.*?<\/span>",self.html)[0]
            src = self.driver.execute_script(f'return $.get("{allpath}")')
            vids=re.findall(r"(ajax\/videosec&b=[A-Za-z0-9]+&v=.*?)'.*?<\/span> ?(.*?)<\/button",src)
            for vpath,player in vids:
                self._videos.append(Video(self,vpath,player))
        return self._videos

    def best_video(self, by_res=True, by_fansub=None, default_res=600, callback=lambda x:None):
        """
        Parametrelerde belirtilmiş en ideal videoyu tespit edip döndürür.

        - by_res: 1080p'ye ulaşmaya çalış
        - by_fansub: belirtilen fansub'u öncelikli tut.
        - default_res: Çözünürlüğü bilinmeyen videoların varsayılan çözünürlüğü.
        - callback: function(hook_dict)
        """
        # Yalnızca desteklenenleri filtrele.
        vids = list(filter(lambda x: x.is_supported, self.videos))

        # Callback fonksiyonu belirtilmişse paslanacak hook_dict
        hook_dict = {
            "current": None,
            "total": len(vids),
            "player": None,
            "status": None,
            "object": self
        }

        # Kaliteli player'a göre sırala
        vids = sorted(vids, key = lambda x: SUPPORTED.index(x.player))
        # Seçilmiş fansub'un videolarını öncelikli tut
        if by_fansub:
            vids = sorted(vids, key = lambda x: x.fansub != by_fansub)

        for i,vid in enumerate(vids.copy(),start=1):
            hook_dict = {**hook_dict, "current": i, "player": vid.player}
            callback({**hook_dict, "status": "üstbilgi çekiliyor"})
            if not vid.is_working:
                callback({**hook_dict, "status": "çalışmıyor"})
                vids.remove(vid)
                continue
            # Çözünürlük önemli değilse ya da max çözünürlük bulunduysa videoyu döndür.
            if not by_res or (vid.resolution or default_res) >= 1080:
                callback({**hook_dict, "current":len(vids), "status": "çalışıyor"})
                return vid
        if vids == []:
            callback({**hook_dict, "player": None, "status": "hiçbiri çalışmıyor"})
            return None
        # 1080+ bulunamadıysa, en yüksek çözünürlüğü seç.
        vid = max(vids, key = lambda x:x.resolution or default_res)
        callback({**hook_dict, "player": vid.player , "status": "çalışıyor"})
        return vid


class Video:
    """
    Bir bölüm adına yüklenmiş herhangi bir videoyu temsil eden obje.

    Öznitelikler:
    - path: Video'nun türkanime'deki hash'li dizin yolu.
    - bolum: Video'nun ait olduğu bölüm objesi.
    - fansub: eğer belirtilmişse, videoyu yükleyen fansub'un ismi.
    - url: Videonun decrypted gerçek url'si, örn: https://youtube.com/watch?v=XXXXXXXX
    """
    def __init__(self,bolum,path,player=None,fansub=None,log_handler=LogHandler):
        self.path = path
        self.player = player
        self.fansub = fansub
        self.bolum = bolum
        self._resolution = None
        self._info = None
        self._url = None
        self._is_working = None
        self.is_supported = self.player in SUPPORTED

        self.ydl_opts = {
          'logger': log_handler,
          'quiet': True,
          'ignoreerrors': 'only_download',
          'retries': 5,
          'fragment_retries': 10,
          'restrictfilenames': True,
          'nocheckcertificate': True,
          'concurrent_fragment_downloads': 5,
        }


    @property
    def url(self):
        if self._url is None:
            src = self.bolum.driver.execute_script(f"return $.get('{self.path}')")
            # şifreli iframe'in encryption parametreleri: base64('{"ct":*,"iv":*,"s":*}')
            cipher = re.findall(r"\/embed\/#\/url\/(.*?)\?status",src)[0]
            plaintext = get_real_url(self.bolum.driver,cipher)
            # "\\/\\/fembed.com\\/v\\/0d1e8ilg"  -->  "https://fembed.com/v/0d1e8ilg"
            self._url = "https:"+json.loads(plaintext)
            self._url = self._url.replace("uqload.io","uqload.com") # .com mirror'unu kullan
        return self._url

    @property
    def info(self):
        if self._info is None:
            assert self.is_supported, "Bu player desteklenmiyor."
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                raw_info = ydl.extract_info(self.url, download=False)
                info = ydl.sanitize_info(raw_info)
            # false-pozitifleri önlemek için.
            if info and info.get("video_ext") == "html":
                info = None
            self._info = info or {}
        return self._info

    @property
    def resolution(self):
        """ Video çözünürlüğünü ara, bulunamadıysa None. """
        if self._resolution is None:
            formats = self.info.get("formats")
            res = self.info.get("resolution")
            if res and re.search(r'\d{2,4}',res):
                res = int(re.findall(r'\d{2,4}',res)[-1])
            elif formats:
                if "height" in formats[0]:
                    res = max(formats,key=lambda x:x.get("height") or 0).get("height")
                elif "format_id" in formats[0]:
                    fid = formats[0].get("format_id")
                    res = {"sd":480, "hd":720, "fhd": 1080, "hq":2160}.get(fid)
            if not res and self.player == "MP4UPLOAD":
                try:
                    v_id = self.info.get("id").split("embed-")[1]
                    r = requests.get(f"https://www.mp4upload.com/{v_id}?method_free=Free+Download")
                    res = int(re.findall(r"infoname.*?<span.*?x (\d+)<",r.text)[0])
                except:
                    pass
            self._resolution = res or 0
        return self._resolution

    @property
    def is_working(self):
        """ Video çalışıyor mu? """
        assert self.is_supported, "Bu player desteklenmiyor."
        if self._is_working is None:
            try:
                self._is_working = self.info not in (None, {})
            except:
                self._is_working = False
        return self._is_working

    @is_working.setter
    def is_working(self,value):
        self._is_working = value

    def indir(self, callback=None, output=""):
        """ info.json'u kullanarak videoyu indir """
        assert self.is_working, "Video çalışmıyor."
        seri_slug = self.bolum.anime.slug if self.bolum.anime else ""
        output = join(output, seri_slug, self.bolum.slug)
        opts = self.ydl_opts.copy()
        if callback:
            opts['progress_hooks'] = [callback]
        #if output:
        opts['outtmpl'] = {'default': output + r'.%(ext)s'}
        with NamedTemporaryFile("w",delete=False) as tmp:
            json.dump(self.info, tmp)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download_with_info_file(tmp.name)
        remove(tmp.name)

    def oynat(self, dakika_hatirla=False ,izlerken_kaydet=False, mpv_opts=[]):
        """ Oynatmak için yt-dlp + mpv kullanıyoruz. """
        assert self.is_working, "Video çalışmıyor."
        with NamedTemporaryFile("w",delete=False) as tmp:
            json.dump(self.info, tmp)
        cmd = [
            "mpv",
            "--no-input-terminal",
            "--msg-level=all=error",
            "--script-opts=ytdl_hook-ytdl_path=yt-dlp,ytdl_hook-try_ytdl_first=yes",
            "--ytdl-raw-options=load-info-json=" + tmp.name,
            "ytdl://" + self.bolum.slug # Kaldığın yerden devam etmenin çalışması için.
        ]
        if dakika_hatirla:
            mpv_opts.append("--save-position-on-quit")
        if izlerken_kaydet:
            mpv_opts.append("--stream-record")
        for opt in mpv_opts:
            cmd.insert(1,opt)
        return sp.run(cmd, text=True, stdout=sp.PIPE, stderr=sp.PIPE)

## Qweren not:
turkanime-indirici'yi forklayıp kendi kullanımım için gui ekledim. belki bir gün mergelenir. turkanime_gui/main.py çalıştırın.

# TürkAnimu-Cli
[![GitHub all releases](https://img.shields.io/github/downloads/kebablord/turkanime-indirici/total?style=flat-square)](https://github.com/KebabLord/turkanime-indirici/releases/latest)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/kebablord/turkanime-indirici?style=flat-square)](https://github.com/kebablord/turkanime-indirici/releases/latest/download/turkanimu.exe)
[![Downloads](https://static.pepy.tech/personalized-badge/turkanime-cli?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Pip%20Installs)](https://pepy.tech/project/turkanime-cli)
[![Pypi version](https://img.shields.io/pypi/v/turkanime-cli?style=flat-square)](https://pypi.org/project/turkanime-cli/)

Türkanime için video oynatıcı, indirici ve kütüphane. İtinayla her bölümü indirir & oynatır.
 - Yığın bölüm indirebilir, indirmeye kaldığı yerden devam edebilir.
 - Animu izleyebilir, izlerken kaydedebilir ve kaldığı dakikadan devam edebilir.
 - Fansub seçebilir, en yüksek çözünürlüğe sahip videoyu bulabilir.

 ### İzleme ekranı
 ![izleme.gif](https://i.imgur.com/s04Dnox.gif)

 ### İndirme ekranı
 ![indirme.gif](https://i.imgur.com/k7Y3LYA.gif)
 
#### Geliştirici misin?
Tüm metodları görmek için [dökümantasyona](https://github.com/KebabLord/turkanime-indirici/wiki) bir göz at derim.
```py
""" Bu API'yı kullanmak bu kadar kolay """
>>> import turkanime_api as ta
# Webdriver'ı başlat
>>> driver = ta.create_webdriver()
# Anime objesini yarat
>>> anime = ta.Anime(driver,"non-non-biyori")
>>> print(anime.info)
{'Anime Türü': ['Okul', 'Yaşamdan Kesitler', 'Seinen', 'Komedi'],
 'Başlama Tarihi': '08 Ekim 2013, Salı',
 'Bitiş Tarihi': '24 Aralık 2013, Salı',
 'Bölüm Sayısı': '13 / 12+',
 'Japonca': 'のんのんびより',
 'Kategori': 'TV',
 'Puanı': 8.54,
 'Resim': 'http://www.turkanime.co/imajlar/serilerb/1825.jpg',
 'Stüdyo': 'Silver Link.',
 'Özet': "İlkokula giden Hotaru Ichijou, ailesiyle birlikte Tokyo'dan "
         'memleketine taşınmıştır. Farklı yaşıtlardaki 5 öğrencinin bulunduğu '
         'yeni okuluna uyum sağlamalıdır.'}
>>> bolum4 = anime.bolumler[3]
>>> bolum4.videos[0].url
'https://drive.google.com/file/d/1E8cy53kiuBg13S30M50m_5yS8xnr9aYf/preview'
```

#### Desteklenen kaynaklar:
```
Sibnet  Odnoklassinki  Sendvid  Mail.ru
VK  Google+  Myvi  GoogleDrive  Yandisk
Vidmoly  Dailymotion  Uqload  MP4upload
```

# Kurulum
Önceden derlenmiş "exe" sürümleri [indirebilir](https://github.com/KebabLord/turkanime-indirici/releases/latest) ya da pip ile kolayca kurabilirsiniz: `py -m pip install turkanime-cli`
Daha fazlası için [wiki sayfasını](https://github.com/KebabLord/turkanime-indirici/wiki/Herhangi-bir-uygulamay%C4%B1-system-path'%C4%B1na-ekleme) ziyaret edebilirsiniz.
Script'in çalışabilmesi için bilgisayarınızda firefox kurulu olmalıdır. Cloudflare korumasını aşabilmenin şimdilik tek yolu bu.

### Yapılacaklar:
 - [ ] İndirme bitimi aksiyonları: bildirim veya bilgisayar kapatma.
 - [ ] Gui versiyon
 - [ ] Selenium'dan kurtulma
 - [x] ~~Maximum çözünürlüğe ulaş.~~
 - [x] ~~Youtube-dl yerine yt-dlp'ye geçilmeli.~~
 - [x] ~~Yeni sürüm var mı uygulama açılışında kontrol et.~~
 - [x] ~~Paralel anime indirme özelliği.~~
 - [x] ~~Progress yaratılma satırı minimal bir class ile kısaltılacak.~~
 - [x] ~~Domain güncellemesinden beridir kod stabil çalışmıyor, düzeltilecek.~~
 - [x] ~~Kod çorba gibi, basitleştirilecek.~~
 - [x] ~~Navigasyon ve indirme algoritması http talepleriyle sağlanacak.~~
 - [x] ~~Zaman bloğu olarak sleep'den kurtulunacak, elementin yüklenmesi beklenecek.~~
 - [x] ~~Prompt kütüphanesi olarak berbat durumda olan PyInquirer'den Questionary'e geçilecek.~~
 - [x] ~~Arama sonuçları da http talepleriyle getirilecek.~~
 - [x] ~~Fansub seçme özelliği tekrar eklenecek.~~

# ING DDP - LDAP Entegrasyonlu Streamlit Uygulaması

Bu proje, LDAP sunucu entegrasyonu ile kullanıcı kimlik doğrulama yapan ve grup kontrolü ile SMS doğrulama adımına geçiş sağlayan modern bir Streamlit uygulamasıdır.

## 🚀 Özellikler

- **LDAP Entegrasyonu**: Kurumsal LDAP sunucuları ile entegrasyon
- **Grup Kontrolü**: Belirli LDAP gruplarındaki kullanıcıları kontrol etme
- **SMS Doğrulama**: İki faktörlü kimlik doğrulama sistemi
- **Modern UI**: ING kurumsal kimliğine uygun arayüz tasarımı
- **Güvenli Giriş**: LDAP tabanlı kullanıcı doğrulama
- **Responsive Tasarım**: Tüm cihazlarda uyumlu çalışma

## 📋 Gereksinimler

- Python 3.8 veya üzeri
- LDAP sunucu erişimi
- İnternet bağlantısı (paket yükleme için)

## 🛠️ Kurulum Adımları

### 1. Repository'yi Klonlayın

```bash
git clone https://github.com/kurnazokan/ddp.git
cd ddp
```

### 2. Virtual Environment Oluşturun (Önerilen)

```bash
# Python venv modülü ile
python3 -m venv venv

# Virtual environment'ı aktifleştirin
# macOS/Linux için:
source venv/bin/activate

# Windows için:
# venv\Scripts\activate
```

### 3. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 4. LDAP Konfigürasyonu

`ldap_config.py` dosyasını kendi LDAP sunucu bilgilerinizle güncelleyin:

```python
LDAP_CONFIG = {
    "server": "ldap://your-ldap-server.com:389",
    "base_dn": "dc=company,dc=com",
    "bind_dn": "cn=admin,dc=company,dc=com",
    "bind_password": "admin_password",
    "group_dn": "cn=allowed_users,ou=groups,dc=company,dc=com",
    "user_filter_attribute": "uid",
    "group_member_attribute": "member"
}
```

#### Environment Variable Kullanımı (Güvenlik için)

```bash
export LDAP_SERVER="ldap://ldap.company.com:389"
export LDAP_BASE_DN="dc=company,dc=com"
export LDAP_BIND_DN="cn=admin,dc=company,dc=com"
export LDAP_BIND_PASSWORD="secure_password"
export LDAP_GROUP_DN="cn=allowed_users,ou=groups,dc=company,dc=com"
```

## 🚀 Uygulamayı Başlatma

### Geliştirme Modunda Çalıştırma

```bash
# Virtual environment aktifse
streamlit run app.py

# Veya doğrudan
python -m streamlit run app.py
```

### Production Modunda Çalıştırma

```bash
# Port belirterek
streamlit run app.py --server.port 8501

# Host belirterek (tüm IP'lerden erişim)
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Docker ile Çalıştırma

```bash
# Dockerfile oluşturun (opsiyonel)
docker build -t ing-ddp .
docker run -p 8501:8501 ing-ddp
```

## 🌐 Erişim

Uygulama başlatıldıktan sonra:

- **Local**: http://localhost:8501
- **Network**: http://your-ip:8501
- **Default Port**: 8501

## 🔐 Kullanım

### 1. Login Ekranı
- Kullanıcı adınızı girin (LDAP'daki kullanıcı adı)
- Şifrenizi girin
- "Giriş Yap" butonuna tıklayın

### 2. LDAP Doğrulama
- Sistem LDAP sunucusunda kullanıcıyı arar
- Şifre doğrulanır
- Kullanıcının belirtilen grupta olup olmadığı kontrol edilir

### 3. SMS Doğrulama
- Başarılı LDAP doğrulama sonrası SMS sayfasına yönlendirilir
- SMS kodunu girin (demo: 1111)
- "Onayla" butonuna tıklayın

### 4. Dashboard
- Başarılı SMS doğrulama sonrası ana dashboard'a erişim

## 📁 Proje Yapısı

```
ing-ddp-ldap/
├── app.py                 # Ana Streamlit uygulaması
├── ldap_config.py         # LDAP konfigürasyon dosyası
├── requirements.txt       # Python bağımlılıkları
├── LDAP_KURULUM.md       # LDAP kurulum kılavuzu
├── README.md             # Bu dosya
└── ing-logo.svg          # ING logo dosyası
```

## 🔧 Konfigürasyon Seçenekleri

### LDAP Sunucu Türleri

#### Active Directory
```python
"user_filter_attribute": "sAMAccountName"
"group_dn": "CN=AllowedUsers,OU=Groups,DC=company,DC=com"
```

#### OpenLDAP
```python
"user_filter_attribute": "uid"
"group_dn": "cn=allowed_users,ou=groups,dc=company,dc=com"
```

## 🐛 Sorun Giderme

### Yaygın Hatalar

1. **LDAP Bağlantı Hatası**
   - Sunucu adresini kontrol edin
   - Port numarasını doğrulayın
   - Firewall ayarlarını kontrol edin

2. **Kimlik Doğrulama Hatası**
   - Admin bilgilerini kontrol edin
   - Base DN'i doğrulayın
   - Kullanıcı filter attribute'unu kontrol edin

3. **Grup Kontrolü Hatası**
   - Group DN'i doğrulayın
   - Grup üyeliği attribute'unu kontrol edin

### Log Kontrolü

```bash
# Streamlit log'larını görüntüleme
streamlit run app.py --logger.level debug
```

## 📚 Ek Kaynaklar

- [LDAP Kurulum Kılavuzu](LDAP_KURULUM.md)
- [Streamlit Dokümantasyonu](https://docs.streamlit.io/)
- [Python LDAP Dokümantasyonu](https://www.python-ldap.org/)

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit yapın (`git commit -m 'Add some AmazingFeature'`)
4. Push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

- **Proje Sahibi**: Okan Kurnaz
- **Repository**: [https://github.com/kurnazokan/ddp](https://github.com/kurnazokan/ddp)

---

**Not**: Bu uygulama LDAP sunucu erişimi gerektirir. Kurulum öncesi LDAP sunucu bilgilerinizi hazırladığınızdan emin olun. 
# LDAP Entegrasyonu Kurulum Kılavuzu

Bu dokümanda, ING DDP uygulamasına LDAP entegrasyonunun nasıl kurulacağı açıklanmaktadır.

## Genel Bakış

Uygulama artık LDAP sunucusunda kullanıcı kimlik doğrulaması yapmakta ve kullanıcının belirli bir grupta olup olmadığını kontrol etmektedir. Sadece gruptaki kullanıcılar SMS doğrulama adımına geçebilir.

## Kurulum Adımları

### 1. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 2. LDAP Konfigürasyonu

`ldap_config.py` dosyasını kendi LDAP sunucu bilgilerinizle güncelleyin:

```python
LDAP_CONFIG = {
    "server": "ldap://your-ldap-server.com:389",  # LDAP sunucu adresi
    "base_dn": "dc=company,dc=com",  # Base DN
    "bind_dn": "cn=admin,dc=company,dc=com",  # Admin bind DN
    "bind_password": "admin_password",  # Admin şifresi
    "group_dn": "cn=allowed_users,ou=groups,dc=company,dc=com",  # Kontrol edilecek grup DN
    "user_filter_attribute": "uid",  # Kullanıcı arama attribute'u
    "group_member_attribute": "member"  # Grup üyeliği attribute'u
}
```

### 3. LDAP Sunucu Türüne Göre Konfigürasyon

#### Active Directory için:

```python
LDAP_CONFIG = {
    "server": "ldap://dc.company.com:389",
    "base_dn": "dc=company,dc=com",
    "bind_dn": "administrator@company.com",
    "bind_password": "admin_password",
    "group_dn": "CN=AllowedUsers,OU=Groups,DC=company,DC=com",
    "user_filter_attribute": "sAMAccountName",
    "group_member_attribute": "member"
}
```

#### OpenLDAP için:

```python
LDAP_CONFIG = {
    "server": "ldap://ldap.company.com:389",
    "base_dn": "dc=company,dc=com",
    "bind_dn": "cn=admin,dc=company,dc=com",
    "bind_password": "admin_password",
    "group_dn": "cn=allowed_users,ou=groups,dc=company,dc=com",
    "user_filter_attribute": "uid",
    "group_member_attribute": "member"
}
```

### 4. Güvenlik Ayarları

- Admin şifresini güvenli bir şekilde saklayın
- LDAP bağlantısı için SSL/TLS kullanmayı düşünün
- Firewall'da LDAP portunu (389) açın

## Çalışma Mantığı

1. **Kullanıcı Girişi**: Kullanıcı kullanıcı adı ve şifresini girer
2. **LDAP Doğrulama**: Sistem LDAP sunucusunda kullanıcıyı arar
3. **Şifre Kontrolü**: Kullanıcı şifresi ile bind olmayı dener
4. **Grup Kontrolü**: Kullanıcının belirtilen grupta olup olmadığını kontrol eder
5. **SMS Adımı**: Başarılı olursa SMS doğrulama sayfasına yönlendirir

## Hata Mesajları

- **"Kullanıcı bulunamadı"**: LDAP'da kullanıcı mevcut değil
- **"Geçersiz kullanıcı adı veya şifre"**: Şifre yanlış
- **"Kullanıcı doğrulandı ancak gerekli grupta değil"**: Kullanıcı grupta değil
- **"LDAP sunucusuna bağlanılamıyor"**: Ağ bağlantı sorunu

## Test Etme

1. Uygulamayı başlatın: `streamlit run app.py`
2. LDAP'da mevcut bir kullanıcı ile giriş yapmayı deneyin
3. Kullanıcının grupta olup olmadığını kontrol edin
4. SMS adımına geçiş yapılıp yapılmadığını doğrulayın

## Sorun Giderme

### Bağlantı Sorunları
- LDAP sunucu adresini kontrol edin
- Port numarasını doğrulayın
- Firewall ayarlarını kontrol edin

### Kimlik Doğrulama Sorunları
- Admin bilgilerini kontrol edin
- Base DN'i doğrulayın
- Kullanıcı filter attribute'unu kontrol edin

### Grup Kontrolü Sorunları
- Group DN'i doğrulayın
- Grup üyeliği attribute'unu kontrol edin
- LDAP ağacında grubun varlığını doğrulayın

## Güvenlik Notları

- Admin şifresini kod içinde hardcode etmeyin
- Environment variable kullanmayı düşünün
- LDAP bağlantısı için SSL/TLS kullanın
- Düzenli olarak admin şifresini değiştirin 
# LDAP Entegrasyonu Kurulum Kılavuzu (ldap3 ile)

Bu dokümanda, ING DDP uygulamasına LDAP entegrasyonunun nasıl kurulacağı açıklanmaktadır. Uygulama `ldap3>=2.9.1` kütüphanesini kullanır.

## Genel Bakış

Uygulama artık LDAP sunucusunda kullanıcı kimlik doğrulaması yapmakta ve kullanıcının belirli bir grupta olup olmadığını kontrol etmektedir. Sadece gruptaki kullanıcılar SMS doğrulama adımına geçebilir.

## Kurulum Adımları

### 1. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

**Not**: `ldap3>=2.9.1` kütüphanesi otomatik olarak yüklenecektir.

### 2. LDAP Konfigürasyonu

`ldap_config.py` dosyasını kendi LDAP sunucu bilgilerinizle güncelleyin:

```python
LDAP_CONFIG = {
    "server": "ldaps://your-ldap-server.com:636",
    "ssl_certificate": "/path/to/ssl/certificate.crt",
    "ssl_verify": True,
    "allow_insecure": False,
    "base_dn": "dc=company,dc=com",
    "user_base_dn": "ou=users,dc=company,dc=com",
    "bind_dn": "cn=admin,dc=company,dc=com",
    "bind_password": "admin_password",
    "group_dn": "cn=allowed_users,ou=groups,dc=company,dc=com",
    "user_filter_attribute": "uid",
    "group_member_attribute": "member"
}
```

### 3. LDAP Sunucu Türüne Göre Konfigürasyon

#### Active Directory (ING Bank) için:

```python
LDAP_CONFIG = {
    "server": "ldaps://bankanet.com.tr:636",
    "ssl_certificate": "/data/starburst/SSL/ldap.crt",
    "ssl_verify": True,
    "allow_insecure": False,
    "base_dn": "DC=domain,DC=bankanet,DC=com,DC=tr",
    "user_base_dn": "OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr",
    "bind_dn": "CN=SVCDATABEES,OU=Users,OU=Applications,DC=domain,DC=bankanet,DC=com,DC=tr",
    "bind_password": "secure_password",
    "group_dn": "CN=StarburstUsers,OU=INGBank Security Groups,OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr",
    "group_auth_pattern": "(&(sAMAccountName=${USER})(memberOf=CN=StarburstUsers,OU=INGBank Security Groups,OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr))",
    "user_filter_attribute": "sAMAccountName",
    "group_member_attribute": "memberOf"
}
```

#### OpenLDAP için:

```python
LDAP_CONFIG = {
    "server": "ldap://ldap.company.com:389",
    "ssl_certificate": None,
    "ssl_verify": False,
    "allow_insecure": True,
    "base_dn": "dc=company,dc=com",
    "user_base_dn": "ou=users,dc=company,dc=com",
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
- Firewall'da LDAP portunu (389/636) açın
- SSL sertifika dosyalarını güvenli konumda saklayın

## Çalışma Mantığı

1. **Kullanıcı Girişi**: Kullanıcı kullanıcı adı ve şifresini girer
2. **LDAP Doğrulama**: Sistem LDAP sunucusunda kullanıcıyı arar
3. **Şifre Kontrolü**: Kullanıcı şifresi ile bind olmayı dener
4. **Grup Kontrolü**: Kullanıcının belirtilen grupta olup olmadığını kontrol eder
5. **SMS Adımı**: Başarılı olursa SMS doğrulama sayfasına yönlendirir

## ldap3 Özellikleri

### SSL/TLS Desteği

```python
# SSL ile bağlantı
server = ldap3.Server(
    "ldap.company.com",
    port=636,
    use_ssl=True,
    tls=ldap3.Tls(
        ca_certs_file="/path/to/certificate.crt",
        validate=ldap3.Tls.validate_ssl_certificate
    )
)
```

### Active Directory Entegrasyonu

```python
# sAMAccountName ile kullanıcı arama
user_filter = "(sAMAccountName=username)"

# memberOf attribute ile grup kontrolü
group_attr = "memberOf"
```

### Hata Yönetimi

```python
try:
    # LDAP işlemleri
    pass
except ldap3.core.exceptions.LDAPBindError as e:
    # Bağlantı hatası
    pass
except ldap3.core.exceptions.LDAPException as e:
    # Genel LDAP hatası
    pass
```

## Hata Mesajları

- **"Kullanıcı bulunamadı"**: LDAP'da kullanıcı mevcut değil
- **"Geçersiz kullanıcı adı veya şifre"**: Şifre yanlış
- **"Kullanıcı doğrulandı ancak gerekli grupta değil"**: Kullanıcı grupta değil
- **"LDAP sunucusuna bağlanılamıyor"**: Ağ bağlantı sorunu
- **"Admin bağlantısı başarısız"**: Admin kimlik bilgileri hatalı

## Test Etme

1. Uygulamayı başlatın: `streamlit run app.py`
2. LDAP'da mevcut bir kullanıcı ile giriş yapmayı deneyin
3. Kullanıcının grupta olup olmadığını kontrol edin
4. SMS adımına geçiş yapılıp yapılmadığını doğrulayın

## Sorun Giderme

### Bağlantı Sorunları
- LDAP sunucu adresini kontrol edin
- Port numarasını doğrulayın (389 veya 636)
- Firewall ayarlarını kontrol edin
- SSL sertifika yolunu doğrulayın

### Kimlik Doğrulama Sorunları
- Admin bilgilerini kontrol edin
- Base DN'i doğrulayın
- Kullanıcı filter attribute'unu kontrol edin
- SSL sertifika geçerliliğini kontrol edin

### Grup Kontrolü Sorunları
- Group DN'i doğrulayın
- Grup üyeliği attribute'unu kontrol edin
- LDAP ağacında grubun varlığını doğrulayın
- group_auth_pattern formatını kontrol edin

## Güvenlik Notları

- Admin şifresini kod içinde hardcode etmeyin
- Environment variable kullanmayı düşünün
- LDAP bağlantısı için SSL/TLS kullanın
- Düzenli olarak admin şifresini değiştirin
- SSL sertifikalarını güvenli konumda saklayın

## ldap3 vs python-ldap

| Özellik | ldap3 | python-ldap |
|---------|-------|--------------|
| Python 3 Desteği | ✅ Tam | ⚠️ Sınırlı |
| SSL/TLS | ✅ Gelişmiş | ✅ Temel |
| Active Directory | ✅ Mükemmel | ⚠️ Orta |
| API | ✅ Modern | ⚠️ Eski |
| Hata Yönetimi | ✅ Detaylı | ⚠️ Temel |
| Performans | ✅ Hızlı | ⚠️ Orta | 
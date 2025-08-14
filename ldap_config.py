# LDAP Yapılandırma Dosyası
# Bu dosyayı kendi LDAP sunucu bilgilerinizle güncelleyin

import os

# Environment variable'dan LDAP bilgilerini al (güvenlik için)
LDAP_CONFIG = {
    # LDAP sunucu adresi ve port
    "server": os.getenv("LDAP_SERVER", "ldap://your-ldap-server.com:389"),
    
    # Base DN - LDAP ağacının kökü
    "base_dn": os.getenv("LDAP_BASE_DN", "dc=example,dc=com"),
    
    # Admin kullanıcı bilgileri (LDAP'a bağlanmak için)
    "bind_dn": os.getenv("LDAP_BIND_DN", "cn=admin,dc=example,dc=com"),
    "bind_password": os.getenv("LDAP_BIND_PASSWORD", "admin_password"),
    
    # Kontrol edilecek grup DN - kullanıcının üye olması gereken grup
    "group_dn": os.getenv("LDAP_GROUP_DN", "cn=allowed_users,ou=groups,dc=example,dc=com"),
    
    # Kullanıcı arama filtresi (genellikle uid veya sAMAccountName)
    "user_filter_attribute": os.getenv("LDAP_USER_FILTER_ATTR", "uid"),
    
    # Grup üyeliği kontrolü için kullanılan attribute
    "group_member_attribute": os.getenv("LDAP_GROUP_MEMBER_ATTR", "member")
}

# Environment variable kullanımı için örnek:
# export LDAP_SERVER="ldap://ldap.company.com:389"
# export LDAP_BASE_DN="dc=company,dc=com"
# export LDAP_BIND_DN="cn=admin,dc=company,dc=com"
# export LDAP_BIND_PASSWORD="secure_password"
# export LDAP_GROUP_DN="cn=allowed_users,ou=groups,dc=company,dc=com"

# Örnek LDAP yapılandırmaları:

# Active Directory için:
# LDAP_CONFIG = {
#     "server": "ldap://dc.company.com:389",
#     "base_dn": "dc=company,dc=com",
#     "bind_dn": "administrator@company.com",
#     "bind_password": "admin_password",
#     "group_dn": "CN=AllowedUsers,OU=Groups,DC=company,DC=com",
#     "user_filter_attribute": "sAMAccountName",
#     "group_member_attribute": "member"
# }

# OpenLDAP için:
# LDAP_CONFIG = {
#     "server": "ldap://ldap.company.com:389",
#     "base_dn": "dc=company,dc=com",
#     "bind_dn": "cn=admin,dc=company,dc=com",
#     "bind_password": "admin_password",
#     "group_dn": "cn=allowed_users,ou=groups,dc=company,dc=com",
#     "user_filter_attribute": "uid",
#     "group_member_attribute": "member"
# } 
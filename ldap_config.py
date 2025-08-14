# LDAP Yapılandırma Dosyası
# Bu dosyayı kendi LDAP sunucu bilgilerinizle güncelleyin

import os
from dotenv import load_dotenv

# .env dosyasını otomatik yükle
load_dotenv()

# Environment variable'dan LDAP bilgilerini al (güvenlik için)
LDAP_CONFIG = {
    # LDAP sunucu adresi ve port (SSL ile)
    "server": os.getenv("LDAP_SERVER", "ldaps://bankanet.com.tr:636"),
    
    # SSL sertifika yolu
    "ssl_certificate": os.getenv("LDAP_SSL_CERTIFICATE", "/data/starburst/SSL/ldap.crt"),
    
    # SSL güvenlik ayarları
    "ssl_verify": os.getenv("LDAP_SSL_VERIFY", "true").lower() == "true",
    "allow_insecure": os.getenv("LDAP_ALLOW_INSECURE", "false").lower() == "true",
    
    # Base DN - LDAP ağacının kökü
    "base_dn": os.getenv("LDAP_BASE_DN", "DC=domain,DC=bankanet,DC=com,DC=tr"),
    
    # Kullanıcı base DN
    "user_base_dn": os.getenv("LDAP_USER_BASE_DN", "OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr"),
    
    # Admin kullanıcı bilgileri (LDAP'a bağlanmak için)
    "bind_dn": os.getenv("LDAP_BIND_DN", "CN=SVCDATABEES,OU=Users,OU=Applications,DC=domain,DC=bankanet,DC=com,DC=tr"),
    "bind_password": os.getenv("LDAP_BIND_PASSWORD", ""),
    
    # Grup authentication pattern (Active Directory için)
    "group_auth_pattern": os.getenv("LDAP_GROUP_AUTH_PATTERN", 
        "(&(sAMAccountName=${USER})(memberOf=CN=StarburstUsers,OU=INGBank Security Groups,OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr))"),
    
    # Kontrol edilecek grup DN
    "group_dn": os.getenv("LDAP_GROUP_DN", "CN=StarburstUsers,OU=INGBank Security Groups,OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr"),
    
    # Kullanıcı arama filtresi (Active Directory için sAMAccountName)
    "user_filter_attribute": os.getenv("LDAP_USER_FILTER_ATTR", "sAMAccountName"),
    
    # Grup üyeliği kontrolü için kullanılan attribute
    "group_member_attribute": os.getenv("LDAP_GROUP_MEMBER_ATTR", "memberOf")
}

# Environment variable kullanımı için örnek:
# export LDAP_SERVER="ldaps://bankanet.com.tr:636"
# export LDAP_SSL_CERTIFICATE="/data/starburst/SSL/ldap.crt"
# export LDAP_SSL_VERIFY="true"
# export LDAP_ALLOW_INSECURE="false"
# export LDAP_BASE_DN="DC=domain,DC=bankanet,DC=com,DC=tr"
# export LDAP_USER_BASE_DN="OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr"
# export LDAP_BIND_DN="CN=SVCDATABEES,OU=Users,OU=Applications,DC=domain,DC=bankanet,DC=com,DC=tr"
# export LDAP_BIND_PASSWORD="your_secure_password"
# export LDAP_GROUP_DN="CN=StarburstUsers,OU=INGBank Security Groups,OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr"

# Örnek LDAP yapılandırmaları:

# Active Directory (ING Bank) için:
# LDAP_CONFIG = {
#     "server": "ldaps://bankanet.com.tr:636",
#     "ssl_certificate": "/data/starburst/SSL/ldap.crt",
#     "ssl_verify": True,
#     "allow_insecure": False,
#     "base_dn": "DC=domain,DC=bankanet,DC=com,DC=tr",
#     "user_base_dn": "OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr",
#     "bind_dn": "CN=SVCDATABEES,OU=Users,OU=Applications,DC=domain,DC=bankanet,DC=com,DC=tr",
#     "bind_password": "secure_password",
#     "group_dn": "CN=StarburstUsers,OU=INGBank Security Groups,OU=IngBankUsers,DC=domain,DC=bankanet,DC=com,DC=tr",
#     "user_filter_attribute": "sAMAccountName",
#     "group_member_attribute": "memberOf"
# }

# OpenLDAP için:
# LDAP_CONFIG = {
#     "server": "ldap://ldap.company.com:389",
#     "ssl_certificate": None,
#     "ssl_verify": False,
#     "allow_insecure": True,
#     "base_dn": "dc=company,dc=com",
#     "user_base_dn": "ou=users,dc=company,dc=com",
#     "bind_dn": "cn=admin,dc=company,dc=com",
#     "bind_password": "admin_password",
#     "group_dn": "cn=allowed_users,ou=groups,dc=company,dc=com",
#     "user_filter_attribute": "uid",
#     "group_member_attribute": "member"
# } 
# DNS and SSL Guide

## DNS Records

### Common DNS Record Types
- **A Record**: Points domain to IPv4 address
- **AAAA Record**: Points domain to IPv6 address
- **CNAME**: Alias pointing to another domain
- **MX Record**: Mail server for the domain
- **TXT Record**: Text data (SPF, DKIM, verification)
- **NS Record**: Nameservers for the domain

### DNS Propagation
DNS changes can take 24-48 hours to propagate globally. To check propagation:
1. Use online tools like whatsmydns.net
2. Clear local DNS cache
3. Check with different DNS resolvers (8.8.8.8, 1.1.1.1)

### Nameserver Changes
When changing nameservers:
1. Update at domain registrar, not hosting
2. Note current settings before changing
3. Wait for full propagation before making other changes
4. TTL affects how quickly changes propagate

## SSL Certificates

### SSL Installation Issues
If SSL is not working:
1. Verify certificate is installed in cPanel > SSL/TLS
2. Check certificate matches the domain
3. Ensure certificate chain is complete
4. Verify port 443 is open
5. Check for mixed content (HTTP resources on HTTPS page)

### Let's Encrypt SSL
Free SSL via Let's Encrypt in cPanel:
1. Go to cPanel > SSL/TLS Status
2. Click "Run AutoSSL"
3. Wait for certificate issuance
4. Verify domain resolves to server IP

### SSL Certificate Errors
Common SSL errors and fixes:
- **NET::ERR_CERT_DATE_INVALID**: Certificate expired, renew it
- **NET::ERR_CERT_COMMON_NAME_INVALID**: Wrong domain on cert
- **Mixed Content**: Update URLs from HTTP to HTTPS
- **Certificate Chain Incomplete**: Install intermediate certificates

## Domain Setup

### Adding a Domain
To add a new domain to hosting:
1. Update nameservers at registrar
2. Add domain in cPanel > Domains or Addon Domains
3. Wait for DNS propagation
4. Install SSL certificate
5. Upload website files

### Subdomain Setup
To create a subdomain:
1. Go to cPanel > Domains > Subdomains
2. Enter subdomain name
3. Document root is auto-created
4. DNS A record is auto-added
5. Upload files to subdomain folder

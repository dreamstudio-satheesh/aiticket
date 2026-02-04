# General Hosting Support

## Account Management

### Disk Space Full
If account is out of disk space:
1. Check usage in cPanel > Disk Usage
2. Clear email trash and spam folders
3. Remove old backups and logs
4. Compress or remove large files
5. Clear cache folders
6. Consider upgrading hosting plan

### Bandwidth Exceeded
If bandwidth limit is reached:
1. Check bandwidth usage in cPanel metrics
2. Identify high-traffic files or pages
3. Optimize images and enable compression
4. Use CDN for static content
5. Block bad bots via .htaccess
6. Consider upgrading plan

### Backup and Restore
For backups in cPanel:
1. Full backup: cPanel > Backup > Download Full Backup
2. Partial backup: Download home directory, databases, or emails separately
3. Restore: Upload backup and contact support for full restore
4. Automated backups depend on hosting provider settings

## Security

### Account Compromised
If hosting account is hacked:
1. Change all passwords immediately (cPanel, FTP, email, database)
2. Scan for malware using cPanel virus scanner
3. Check for unknown files, especially in uploads folder
4. Review cron jobs for suspicious entries
5. Update all CMS and plugins
6. Check .htaccess for redirects
7. Contact support for malware cleanup if needed

### Blocking IP Addresses
To block an IP in cPanel:
1. Go to cPanel > IP Blocker
2. Enter IP address or range
3. Click Add
Or use .htaccess: deny from IP_ADDRESS

## File Management

### FTP Connection Issues
If FTP is not connecting:
1. Verify FTP credentials (not cPanel credentials)
2. Use correct port: 21 (FTP) or 22 (SFTP)
3. Try passive mode in FTP client
4. Check if IP is blocked
5. Verify FTP server is running

### File Permissions
Recommended permissions:
- Files: 644
- Folders: 755
- wp-config.php: 600 (WordPress)
- .htaccess: 644
Never use 777 - it's a security risk

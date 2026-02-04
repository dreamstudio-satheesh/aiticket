# cPanel Common Issues

## Email Issues

### Cannot Send Emails
If a user cannot send emails from cPanel:
1. Check if the email account exists and password is correct
2. Verify SMTP settings: server, port 465 (SSL) or 587 (TLS)
3. Check if the domain has valid MX records
4. Verify SPF and DKIM records are configured
5. Check mail queue for stuck emails
6. Review /var/log/exim_mainlog for errors

### Cannot Receive Emails
If emails are not being received:
1. Verify MX records point to the correct server
2. Check disk quota - mailbox might be full
3. Review spam filters and BoxTrapper settings
4. Check email routing in cPanel (Local vs Remote)
5. Verify the email account exists

### Email Going to Spam
To improve email deliverability:
1. Set up SPF record: v=spf1 +a +mx +ip4:SERVER_IP ~all
2. Enable DKIM in cPanel > Email Deliverability
3. Set up DMARC record
4. Avoid spam trigger words in subject/body
5. Use consistent From address

## Website Issues

### 500 Internal Server Error
Common causes and fixes:
1. Check .htaccess for syntax errors
2. Verify file permissions (644 for files, 755 for folders)
3. Check PHP version compatibility
4. Review error_log in public_html
5. Increase PHP memory limit if needed

### Website Loading Slowly
To diagnose slow website:
1. Check server resource usage in cPanel metrics
2. Review access logs for excessive requests
3. Check for malware or compromised files
4. Optimize database tables
5. Enable caching (browser, page cache)
6. Check if hitting PHP worker limits

## Database Issues

### Cannot Connect to Database
If website shows database connection error:
1. Verify database credentials in config file
2. Check if database user has correct privileges
3. Verify database server is running
4. Check if database exists and is not corrupted
5. Review MySQL error logs

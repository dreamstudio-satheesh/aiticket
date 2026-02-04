# WHMCS Basics

## What is WHMCS
WHMCS is a web hosting automation platform that handles billing, support tickets, and client management for hosting companies. It integrates with control panels like cPanel and DirectAdmin.

## Common WHMCS Issues

### Invoice Not Generated
If an invoice was not generated automatically:
1. Check if the service is set to auto-generate invoices
2. Verify the billing cycle and next due date
3. Check Automation Settings > Invoice Creation
4. Run the cron job manually if needed

### Client Cannot Login
If a client cannot access their WHMCS client area:
1. Verify the email address is correct
2. Use the password reset function
3. Check if the account is suspended or closed
4. Clear browser cache and cookies
5. Check for IP blocks in Configuration > Security

### Service Not Provisioning
If a hosting account is not being created automatically:
1. Check the server connection in Setup > Servers
2. Verify API credentials for the control panel
3. Check the module debug log for errors
4. Ensure the product is linked to a server group
5. Verify nameservers are configured correctly

## WHMCS Cron Jobs
The WHMCS cron job should run every 5 minutes. It handles:
- Invoice generation
- Service provisioning
- Suspension/termination
- Email reminders
- Domain synchronization

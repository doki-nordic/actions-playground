

List of services:

Service | Port | Client port |Description
--------|------|----------|--
term    | 80   | 9980 | Terminal over HTTP
browser | 81   | 9981 | File browser over HTTP
ssh     | 22   | 9922 | SSH + SFTP
rdp     | 3389 | 9989 | Remote Desktop (Window only)


Secrets only:
* `PASSWORD`
* Zrok
  * `ZROK_TOKEN`
* ZeroTier
  * `ZEROTIER_NETWORK_ID`
  * `ZEROTIER_ACCESS_TOKEN`


* `IP`
* `TERM_ENDPOINT`
* `TERM_PORT`
* `TERM_CLIENT_PORT`
* `FILES_ENDPOINT`
* `FILES_PORT`
* `FILES_CLIENT_PORT`
* `SSH_ENDPOINT`
* `SSH_CLIENT_PORT`
* `RDP_ENDPOINT`
* `RDP_CLIENT_PORT`
* `SSH_KEYS`

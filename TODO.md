

Some TODOs:
* Create seperate repo with ZeroTier action different than https://github.com/marketplace/actions/zerotier
  * It has archive with binaries for each platform (extracted from dep or msi, downloaded from offitial source during the build)
    * https://superuser.com/questions/307678/how-do-i-extract-files-from-an-msi-package
  * The identity is taken from parameters, not generated automatically
  * The identity can be a string (`identity-str` parameter) or a file (`identity-file` parameter)
  * Optionally, if identity is a file and it does not exists, a new identity is created and save to that file.
  * Start process as daemon (in while loop to recover after restart).
  * Optionally, if auth_token is provided, authorize member to ZeroTier network using REST API. (or not if it is not used)
* Simplify key generation:
  * After creating new fork, user have to provide `PASSWORD` and `NETWORK_ID` secrets,
    * optionally `ZEROTIER_AUTH_TOKEN` (or not, because accepting is also simple and additionally you can see newlly assinged IP address)
    * optionally `CLIENT_KEYS` with additional user-generated client public keys.
  * Warn user about missing secrets and show instructions.
  * Keys will be saved in the repo in a special branch with one orphan commit.
  * The first run is detected by invalid `PASSWORD` when trying to decrypt keys
  * On the first run action will:
    * create a SSH host keys
    * create 3 client keys (instruction in docs how to create more keys)
    * start ZeroTier action with missing identity file to create new one
    * pack into two encrypted ZIP files: `user.zip` with all private client keys, `system.zip` with all others
    * commit (ammend) ZIP files to special branch.
    * publish user.zip as artifact
  * If user is interested in keys, he can download `user.zip` file.

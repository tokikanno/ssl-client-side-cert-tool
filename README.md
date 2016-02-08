# ssl-client-side-cert-tool

This is a simple python script for fast generating CA/client keys for SSL client side certification.

# pre-requirements

The only dependency is `fabric`, use `pip install fabric` to install it.

# Show help

After fabric installed, chdir to the git repo root, and simply run `fab -l`, then your could see all available commands here

```
fab -l

Available commands:

    gen_ca_key      generate CA cert keys
    gen_client_key  generate client cert files, user email need be provided.
    revoke_cert     revoke client cert by email, will also update crl.cem file and delete the client cert folder
    update_crl      update crl.pem file
```

# Basic usage

### 1. Generate CA key pairs
For the 1st time using it, you'll need to generate the CA key pais fisrt. Simply run the following command will do this.

```
fab gen_ca_key
```

After successfully executed, `ca.crt` & `ca.key` will be generated automatically. 
**Caution: You should take a look in fabfile.py and change the `_DEFAULT_SUBJ_TPL` as you need.**

### 2. Generate client keys

After the ca key paris created, you may start generating client keys. A client email need to be provied. Use a `:` for passing the email to the fabric function.

```
fab gen_client_key:test@test.com
```

After that, a folded based on user email will be created, and inside it will have following files


* client.key - the client private key
* client.crt - the client cert file
* sign.crt   - the ca-signed client cert file, it will be used for generating client.p12/client.pem
* client.p12 - client cert file for operating systems (eg: Windows, OSX)
* client.pin - for security reason, some OS will force asks for a export pin code, a 4 digits pin code will be randomly generated and saved in this file.
* client.pem - client cert file in pem format, could be used for curl with following command `curl -k -cacert client.pem https:/xxx.xxx`

Generally, you should send the `client.p12` and the 4 digits pincode in `client.pin` to your user.

### 3. Generate initial crl.pem (Only need to do once)

The following command will generate an empty revoke list file `index.txt` and signed crl file `crl.pem`

```
fab update_crl
```

# Setup the web server

We'll use nginx as our example web server.

To activate SSL client side certification, add following lines into your nginx site configuration file.

```
ssl_client_certificate /path/to/ca.crt;
ssl_verify_client optional;
ssl_crl /path/to/crl.pem;
```

and this if block for checking if the client passed the SSL verification

```
if ($ssl_client_verify != SUCCESS){
  return 403;
}
```

# Revoke client certification

To revoke single client certification, use following command

```
fab revoke_cert:test@test.com
```

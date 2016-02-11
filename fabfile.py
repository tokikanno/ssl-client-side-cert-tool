from fabric.api import local
from fabric.colors import blue, green, red
import random
import string
import os
import shutil


_CA_CN = 'pinkoi.com'
_CLIENT_FOLDER = 'client'
_DEFAULT_SUBJ_TPL = '"/C=TW/ST=Taiwan/L=Taipei/O=Pinkoi Inc./OU=Dev/CN=%s"'
_PIN_LENGTH = 4


def _gen_export_pincode():
    return ''.join(random.choice(string.digits) for x in xrange(_PIN_LENGTH))


def _printkv(k, v):
    print blue(k), green(v)


def _get_client_folder(email):
    return '%s/%s' % (_CLIENT_FOLDER, email)


def gen_ca_key():
    '''
    generate CA cert keys
    '''
    ctx = {
        'subj': _DEFAULT_SUBJ_TPL % _CA_CN,
    }

    local('openssl req -new -newkey rsa:4096 -x509 -days 365 -nodes -keyout ca.key -out ca.crt -subj %(subj)s' % ctx)
    local('chmod 600 ca.crt ca.key')


def gen_client_key(email):
    '''
    generate client cert files, user email need to be provided.
    '''
    assert email and '@' in email and '.' in email
    _printkv('email:', email)

    ctx = {
        'epwd': _gen_export_pincode(),
        'subj': _DEFAULT_SUBJ_TPL % email,
        'email': email,
        'client_path': _get_client_folder(email)
    }

    if not os.path.exists(ctx['client_path']):
        os.makedirs(ctx['client_path'])
    print green('user key dir (%(client_path)s) created' % ctx)
    print blue('generating client key')

    local('openssl req -new -newkey rsa:4096 -nodes -keyout %(client_path)s/client.key -out %(client_path)s/client.crt -subj %(subj)s' % ctx)
    local('chmod 600 %(client_path)s/client.key %(client_path)s/client.crt')

    print blue('signing with ca.key')
    local('openssl x509 -req -days 365 -in %(client_path)s/client.crt -CA ca.crt -CAkey ca.key -CAcreateserial -CAserial ca.serial -out %(client_path)s/sign.crt' % ctx)

    print blue('generating p12')
    local('openssl pkcs12 -export -clcerts -in %(client_path)s/sign.crt -inkey %(client_path)s/client.key -out %(client_path)s/client.p12 -passout pass:%(epwd)s' % ctx)

    print blue('generating pem')
    local('openssl pkcs12 -in %(client_path)s/client.p12 -out %(client_path)s/client.pem -clcerts -passin pass:%(epwd)s -nodes' % ctx)

    _printkv('export password', ctx['epwd'])
    with open('%(client_path)s/client.pin' % ctx, 'w') as f:
        f.write(ctx['epwd'])

    print green('done')


def revoke_cert(email):
    '''
    revoke client cert by email, will also update crl.pem file and delete the client cert folder

    DO remember restart web server after clr.pem updated
    '''
    assert email and '@' in email and '.' in email

    ctx = {
        'email': email,
        'client_path': _get_client_folder(email)
    }

    if not os.path.exists(ctx['client_path']):
        print red('user %(email)s not exists' % ctx)
        return

    print 'revoking client cert of %(email)s' % ctx
    local('openssl ca -config ca.conf -revoke %(client_path)s/sign.crt -keyfile ca.key -cert ca.crt' % ctx)

    print 'deleting client cert directory'
    shutil.rmtree(ctx['client_path'])

    update_crl()


def update_crl():
    '''
    update crl.pem file

    DO remember restart web server after clr.pem updated
    '''
    if not os.path.exists('index.txt'):
        print 'no index.txt found, will create an empty one'
        with open('index.txt', 'w') as f:
            f.close()

    print 'updating crl.pem'
    local('openssl ca -config ca.conf -gencrl -out crl.pem')
    print green('Done, ') + red('DO REMERMBER RELOAD Nginx!')

from fabric.api import local
from fabric.colors import blue, green, red
import random
import string
import os


_CA_CN = 'pinkoi.com'
_DEFAULT_SUBJ_TPL = '"/C=TW/ST=Taiwan/L=Taipei/O=Pinkoi Inc./OU=Dev/CN=%s"'
_PIN_LENGTH = 4


def _gen_export_pincode():
    return ''.join(random.choice(string.digits) for x in xrange(_PIN_LENGTH))


def _printkv(k, v):
    print blue(k), green(v)


def gen_ca_key():
    '''
    generate CA cert keys
    '''
    ctx = {
        'subj': _DEFAULT_SUBJ_TPL % _CA_CN,
    }

    local('openssl req -new -newkey rsa:4096 -x509 -days 365 -nodes -keyout ca.key -out ca.crt -subj %(subj)s' % ctx)


def gen_client_key(email):
    '''
    generate client cert files, user email need be provided.
    '''
    assert email and '@' in email and '.' in email
    user = email.split('@')[0]
    _printkv('email:', email)
    _printkv('user:', user)

    if not os.path.exists(user):
        os.mkdir(user)
    print green('user %s key dir created' % user)
    print blue('generating client key')

    ctx = {
        'epwd': _gen_export_pincode(),
        'subj': _DEFAULT_SUBJ_TPL % email,
        'user': user,
    }
    local('openssl req -new -newkey rsa:4096 -nodes -keyout %(user)s/client.key -out %(user)s/client.crt -subj %(subj)s' % ctx)

    print blue('signing with ca.key')
    local('openssl x509 -req -days 365 -in %(user)s/client.crt -CA ca.crt -CAkey ca.key -CAcreateserial -CAserial ca.serial -out %(user)s/sign.crt' % ctx)

    print blue('generating p12')
    local('openssl pkcs12 -export -clcerts -in %(user)s/sign.crt -inkey %(user)s/client.key -out %(user)s/client.p12 -passout pass:%(epwd)s' % ctx)

    print blue('generating pem')
    local('openssl pkcs12 -in %(user)s/client.p12 -out %(user)s/client.pem -clcerts -passin pass:%(epwd)s -nodes' % ctx)

    _printkv('export password', ctx['epwd'])
    with open('%(user)s/client.pin' % ctx, 'w') as f:
        f.write(ctx['epwd'])

    print green('done')


def revoke_cert(email):
    '''
    remove client cert by email
    '''
    assert email and '@' in email and '.' in email
    user = email.split('@')[0]
    _printkv('email:', email)
    _printkv('user:', user)

    ctx = {
        'user': user,
    }

    if not os.path.exists(user):
        print red('user %(user)s not exists' % ctx)
        return

    print 'revoking client cert of %(user)s' % ctx
    local('openssl ca -config ca.conf -revoke %(user)s/sign.crt -keyfile ca.key -cert ca.crt' % ctx)

    update_crl()


def update_crl():
    '''
    update crl file
    '''
    if not os.path.exists('index.txt'):
        print 'no index.txt found, will create an empty one'
        with open('index.txt', 'w') as f:
            f.close()

    print 'updating crl.pem'
    local('openssl ca -config ca.conf -gencrl -out crl.pem')
    print green('Done, ') + red('DO REMERMBER RELOAD Nginx!')


import math
import hashlib

from sympy import isprime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import dsa


class _PseudoGenerator:

    def __init__(self, password: 'bytes|str', salt: 'bytes|str',):
        if type(password) is str:
            password = password.encode('utf-8')
        if type(salt) is str:
            salt = salt.encode('utf-8')
        seed = hashlib.pbkdf2_hmac('sha512', password, salt, 10000)
        self.hash_salt = hashlib.pbkdf2_hmac('sha512', seed, salt, 100)
        h = hashlib.sha512(seed)
        h.update(self.hash_salt)
        self.state = h.digest()
        self.consumed = 0
        self.password = password
        self.salt = salt

    def random_chunk(self, length: int) -> bytes:
        if self.consumed == len(self.state):
            h = hashlib.sha512(self.state)
            h.update(self.hash_salt)
            self.state = h.digest()
            self.consumed = 0
        ret = self.state[self.consumed:self.consumed + length]
        self.consumed += len(ret)
        return ret

    def random_bytes(self, length: int) -> bytes:
        ret: bytearray = bytearray()
        while length > 0:
            chunk = self.random_chunk(length)
            ret.extend(chunk)
            length -= len(chunk)
        return ret

def _convert_private_key(private_key, public_key_name: str) -> 'tuple[str, str]':
    prv = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    pub = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    ).decode()
    parts = pub.split(' ')
    if len(parts) == 2:
        pub = pub.strip() + ' ' + public_key_name
    return (prv, pub)


def generate_rsa(password: 'bytes|str', public_key_name: str, key_size: int) -> 'tuple[str, str]':

    assert(key_size >= 512)
    assert(key_size % 16 == 0)

    def generate_prime(rng: _PseudoGenerator, size, prev_msb = None):
        i = 0
        while True:
            i += 1
            #print('--', i)
            # Generate q candidate, most significant byte should be >= 0xB6 to ensure key_size bits
            # For simplicity ensure it is >= 0xC0, which does not require multiple
            prime_bytes = rng.random_bytes(size // 8)
            prime_bytes[0] |= 0xC0
            # If q is too close to p, shift q away from p, it will be still >= 0xB6
            if (prev_msb is not None) and (prime_bytes[0] < prev_msb + 2):
                prime_bytes[0] -= 3
            # Make sure p is odd
            prime_bytes[-1] |= 1
            # Make sure p is prime
            prime = int.from_bytes(prime_bytes, 'big')
            if isprime(prime):
                return (prime, prime_bytes[0])
            
    def lcm(a, b):
        return abs(a * b) // math.gcd(a, b)

    rng = _PseudoGenerator(password, f'RSA-{key_size}')

    # Assume p size and q size is half of key size
    half = key_size // 2

    (p, p_msb) = generate_prime(rng, half)
    (q, _) = generate_prime(rng, half, p_msb)

    # Swap p and q if necessary to make p > q
    if p < q:
        (p, q) = (q, p)

    n = p * q
    l = lcm(p - 1, q - 1)
    e = 0x10001
    d = pow(e, -1, l)

    iqmp = rsa.rsa_crt_iqmp(p, q)
    dmp1 = rsa.rsa_crt_dmp1(d, p)
    dmq1 = rsa.rsa_crt_dmq1(d, q)

    private_key = rsa.RSAPrivateNumbers(
        p=p,
        q=q,
        d=d,
        dmp1=dmp1,
        dmq1=dmq1,
        iqmp=iqmp,
        public_numbers=rsa.RSAPublicNumbers(e=e, n=n)
    ).private_key()

    return _convert_private_key(private_key, public_key_name)


def generate_ed25519(password: 'bytes|str', public_key_name: str) -> 'tuple[str, str]':

    rng = _PseudoGenerator(password, b'Ed25519')
    private_bytes = rng.random_bytes(32)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)

    return _convert_private_key(private_key, public_key_name)


def generate_ecdsa(password: 'bytes|str', public_key_name: str, curve: ec.EllipticCurve) -> 'tuple[str, str]':

    def ec_get_n(curve: ec.EllipticCurve):
        name = curve.name
        if name == 'prime192v1':
            return 0xffffffffffffffffffffffff99def836146bc9b1b4d22831
        if name == 'prime256v1':
            return 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
        if name == 'secp192r1':
            return 0xffffffffffffffffffffffff99def836146bc9b1b4d22831
        if name == 'secp224r1':
            return 0xffffffffffffffffffffffffffff16a2e0b8f03e13dd29455c5c2a3d
        if name == 'secp256r1':
            return 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
        if name == 'secp384r1':
            return 0xffffffffffffffffffffffffffffffffffffffffffffffffc7634d81f4372ddf581a0db248b0a77aecec196accc52973
        if name == 'secp521r1':
            return 0x1fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa51868783bf2f966b7fcc0148f709a5d03bb5c9b8899c47aebb6fb71e91386409
        if name == 'secp256k1':
            return 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
        if name == 'sect163k1':
            return 0x4000000000000000000020108a2e0cc0d99f8a5ef
        if name == 'sect233k1':
            return 0x8000000000000000000000000000069d5bb915bcd46efb1ad5f173abdf
        if name == 'sect283k1':
            return 0x1ffffffffffffffffffffffffffffffffffe9ae2ed07577265dff7f94451e061e163c61
        if name == 'sect409k1':
            return 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffe5f83b2d4ea20400ec4557d5ed3e3e7ca5b4b5c83b8e01e5fcf
        if name == 'sect571k1':
            return 0x20000000000000000000000000000000000000000000000000000000000000000000000131850e1f19a63e4b391a8db917f4138b630d84be5d639381e91deb45cfe778f637c1001
        if name == 'sect163r2':
            return 0x40000000000000000000292fe77e70c12a4234c33
        if name == 'sect233r1':
            return 0x1000000000000000000000000000013e974e72f8a6922031d2603cfe0d7
        if name == 'sect283r1':
            return 0x3ffffffffffffffffffffffffffffffffffef90399660fc938a90165b042a7cefadb307
        if name == 'sect409r1':
            return 0x10000000000000000000000000000000000000000000000000001e2aad6a612f33307be5fa47c3c9e052f838164cd37d9a21173
        if name == 'sect571r1':
            return 0x3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe661ce18ff55987308059b186823851ec7dd9ca1161de93d5174d66e8382e9bb2fe84e47
        if name == 'brainpoolP256r1':
            return 0xa9fb57dba1eea9bc3e660a909d838d718c397aa3b561a6f7901e0e82974856a7
        if name == 'brainpoolP384r1':
            return 0x8cb91e82a3386d280f5d6f7e50e641df152f7109ed5456b31f166e6cac0425a7cf3ab6af6b7fc3103b883202e9046565
        if name == 'brainpoolP512r1':
            return 0xaadd9db8dbe9c48b3fd4e6ae33c9fc07cb308db3b3c9d20ed6639cca70330870553e5c414ca92619418661197fac10471db1d381085ddaddb58796829ca90069
        raise ValueError('Unsupported EC curve')

    rng = _PseudoGenerator(password, f'EC-{curve.name}')
    n = ec_get_n(curve)
    bytes_size = (curve.key_size + 7) // 8
    clean_mask = 0xFF >> (8 * bytes_size - curve.key_size)
    while True:
        key_bytes = rng.random_bytes(bytes_size)
        key_bytes[0] &= clean_mask
        key_value = int.from_bytes(key_bytes, 'big')
        if (key_value > 0) and (key_value < n):
            break
    private_key = ec.derive_private_key(key_value, curve)

    return _convert_private_key(private_key, public_key_name)


def generate_dsa(password: 'bytes|str', public_key_name: str, key_size: int) -> 'tuple[str, str]':

    def dsa_get_pqg(key_size):
        if key_size == 1024:
            return (
                0xfb3bd0f33438dcf5ba680dd7e3116e92c578d3a05158cdafdd9ab321b18837f6670239404b84e06988ad849126485a2be8f927ae6d24a77d956db49ec2c4f2c5b5433da66e3861f1d66c339528e498d1b804a6a590bf3dfd404cdfc4687e05cf362a7a986043d27c03bd91351160ecb5f036315557c6b6e68754a1fb81a3b9d3,
                0xffbff3a2b59dc314e9aa1b6f44e6e2c2adcdda7f,
                0x99a8cadcc64a611c6a011d2b3480a4ab42ed5e6c4dccfa22eaaa2dc07a6d775b5c55b01cc835ba7986040ef5a80d3c57e9f07f1078acbd8a23adc7eaef93a38ec98b4fcdb0275c5c69fbcf50af05fed72e4751f03cb62822fa81c243229c9cd9dfa358d8dc38505192286523bb5d7b76de847827f9019c883389896da03be218
            )
        if key_size == 2048:
            return (
                0xfd44093c034f911a70bc3c3af27f92a67c3a2649d13ba20922f5f120e5b81b79490148a09bdc748af0b463638cff2c1630ebf60e5bd30677b2b2946dad6f427808d73cbe414547b8ba0b1cc132f1030a31dad05bbddf050b6d3a186874c76f0cbc9704a68eba6c58e2d0ca7b3732cf90a1b8e0fac19daaa96c51d90d8d69d15c8203aea7f610c1cb717dcbbec7497bcfc74b61aab12be08be50495984f9dfcc540e94b926778cc9f5b18a7a51823e781c3bfb4f49e533b2ecc86e78272c2bef23e49a1bfbd91a569c3c53ad805a3b2e47d8b237f8569aeb68dd5023027cfd3baf9ed03277fa30c739b3a27de8b0e7e0feb0a2ec8238ecc1e4324898cdda42193,
                0xffeab9becd16bb022edcfc91189bd5e11beaa6e0a0784213b1ffa4da99e94e4f,
                0x7c4b9b69cefd47fd3f6a8fe1e439ddb49551b10946e9072bd7d92074a7acf59a456b6c9a5e07208dc745f783feec61db36b6db68c962d1adc5beb83d1452379706048ae37355e3bfe592f9fb765533684a537ea5f01a74ef76609e9fe1c23b4f245c181ec9d0013bc091c421ba5b1bed4dda8b3048fd7e416ebc8a30eb992d4251f91b2492460b9bd801e268fe7d84b9e1ae9f6478e7e3d391b4479119af3e83970f17d8fa1c0293040732f3f4a3374e755f8395ec8557a113986bb18395abcc08cae78d946f6890440cd405acc909df0bc36b5ff523a928869ed9e4afe90513ba1058de233cd9375976055fbb47fd70a5cdff5936fd927958dbb0c6636417fe
            )
        if key_size == 3072:
            return (
                0xe197b2cfc6672b73a47cfeaa1f6ccb6d75746d4b47603d80a726f33cda787a2115c859ed1a0c4fc5327c311346bed1c53e6622817cb7a890e93814af936a4cc7e7a3dd682446188e27c2945bd254729528c13d69fd5b20427bd14d4bf926e049ba957665589d4dea2f843dbb33110d84b8e57ab6dc2005a1a00e0695de6e9a210b50803926071ccf85332cf0a0bcf3ffd3040fffa43a590cafb777106c2dcaf1e1b706bf12a65ad17c30cb198aea25dae97eae7973e5607f521c0a1b253482d86f62e7a35578872c0125a46f36cb74f5781789d844c8757f16ca3ab84e531f5de4b6111182a28e27cc09d94eb3bfd0b19e9dc2b981b0e3c85c5fd43543149a4a065a63d1252673a79c10ba7f68d5ad6f890dbc45fe7d03ffb6eb5cfd71a4b18e426102729ded42783524438153df071d72b45b315e24167d9101f00a06b6faa2256dab58aa7f284358298207293c8033f612eebfb70f906b614ba6fbc6680218c38544e0856aeba0763c0e4519af8b138f9531864be74786bb37b2e89061cd75,
                0xfeea0843bd617f31eb94fc53ca6746395d05941fd31096c7d6f86de7a410a445,
                0x312e6744ef0a00259eaec75eedc89222f6efb556497e2c2caf77acbc7eb874bb6247441918472ae625f294e2ae689ac1f4118f791b2c8debd28ff0823f1d77758e5b3a8d7c855a5f49925c0eb3678c802105dfa8558c3f25c238879ef89a28da4dfdc1ebc39c31abdfb0455d3978f2c1d91398b71c3817e9ee5f9753e3358e6f29df5d09df5cdadc51829e2a0da7b1014f652af440e343aef550788cdb77d48902443d153ac878f9c11c82acc6b1c01fe5b06beb404fc6456cb231504ac978a322589c1aa38a5e11d94878ec9c6cf10a9ff9ce555f0dd15e7349656441fac55c7c910dca3de24158592a9e9c3a221c5b139065684d9b8081fb1ec52f401977aa3c96aaff6ee6bf2bcaaf519eaf56e3a50fe4623c1ea27dc2b50fef01254440eebe92a1a45d3d329ccfd38f4bd20f3e93f0326fa5d439d2eb8d460a3ce7c39fda003cfe27241438282cbdf90d12f158589e996012561a0fd344e4f648686626be8067f314c7aabae89597d3f608f28adcfb27cc23a48ba86ee2cb515bc8142f82
            )
        if key_size == 4096:
            return (
                0xd10a31a27042081d5da33972dd0426769460e01e6c791c0692b19a6c5c5dff084a109764086a3043e60394df0c37ee6917c56081d536a05da291b4660acac7affa70aeee9b67f06c7ce84a9cba8687f442f77ea5fe25a75f335f0b6f95e2d087fdfffe9f78f4805612c2c0b6249da30e3005f2ebb3414a3c6b8f79ad4982aed64987389e93246f18c04500d59291aa53cacfcde48e9b80bb37e1b79514ff9b82132294c4e07963540223d707b2a9f96f0fb2bb32edd4472d09b61147fb15e755d360ce48d54f3926eb9c54fc4969dd6c9654de08115028fc964049a77811eed11ca1782885911840fc0011fb2b5827559daea015b33c9a1493ab7822a7a24d513877d5679f040a0a3b858e79ebf368646a60b9caf121074d0d1341543772bbfa27b497c8007ac1106b3634ae932240e5167b6b9a39e93a1d106642630771fb19e48c255255d74e7b261059737d15089692849dae0153a570ca423dc2b3954bebf58b8f8106863ed02a19a2c01f4f5b823f68a8e289c9a6f59dade8fe61f6ee5f1016f53de10e7c450bad5aa10561388862939634dec2177d2a0e2d6f205e2ec3ccb6dfa3aa44f1c85279e4e572a200b38f654e2d593d90fed68254bec39fd261b34fb348a270eb106a3f2e8c836479b9fd5a0dc0d0fee9f6ca424b0a79e0ca56052e3740f52df31dfa29ee56594a3f423f43d4b3a725d608e12e64a2e35a884b,
                0xfaf963c3f501bf845178a9f13efb9fde64e2cc4b5982b5d90443158696844bd7,
                0x6040dd1ea5a3fba0f997ff56574bf39d35491f828d24e6ba7729aa6057d2b741f990c130572cd7b9224a1ac686802e4f82a766ef70cabcd9530af1d334f0bf56fb6f5cf014b245ea84315090bbe4a88aff568a10ee4fe20101950f1f6ca516dc9bdd3f6dc0a5fa482f455d72269d9a1becbf9dc6cd73e4eb6d7433e753f5c59b26cc3c11809734bd6e88711fa3b7faab0f05718fec777af2a08176a94c84d5a8c2b50c25d010f17e0d5933a3aaa249bc0d1959d5ed3fbe03ab61b5fd998c8c450e56bed6af37b7f06104d1d353bdd30aa3435b1f6c7f2611419b5ba23b7fb1b925af5473e8c9650ca380e1f0491bfa0bdc23bdf916c46a36d9a9a1a1a7aeb5ab2c0c16b8c8088a53a741b8e440c81e59119e0ef54727b6e74f4e1ecae7191b8003b615ddfbe7dbca7441ade33f70fe6933613b3de95ff8dfffd3613524f88f0cde787cb5dc547b75faaf89e58cfe25a165f57593e38e17813854fbe11e52353cfe6c245e9c0642d709fba2e2a769589857a2182ca364cd54e100831c16d624d29f05d5b19b060a61ea9311d59141d053296b5879589d0fd202212aedd138b63249c370ec11f21c08a5c960f708d784cbcdea27046c0a2a51c6c991f958b796aa121c7da53c26b8daaec74fe75bdbb943000abfb7def2825e4773206d5268b058556f6d628726ab8c2c275cd4afed5f514c0829d885fe6f7bc294727fb13869a3
            )
        raise ValueError('Invalid DSA key size')

    rng = _PseudoGenerator(password, f'DSA-{key_size}')
    (p, q, g) = dsa_get_pqg(key_size)
    x_bytes_size = (q.bit_length() + 7) // 8
    clean_mask = 0xFF >> (8 * x_bytes_size - q.bit_length())
    while True:
        x_bytes = rng.random_bytes(x_bytes_size)
        x_bytes[0] &= clean_mask
        x = int.from_bytes(x_bytes, 'big')
        if (x > 0) and (x < q):
            break
    y = pow(g, x, p)
    private_key = dsa.DSAPrivateNumbers(
        x=x,
        public_numbers=dsa.DSAPublicNumbers(y=y, parameter_numbers=dsa.DSAParameterNumbers(p=p, q=q, g=g))
    ).private_key()

    return _convert_private_key(private_key, public_key_name)


##################################
#   Experiments and generators   #
##################################


# for key_size in (3072,): #(1024, 2048, 3072, 4096):
#     max_params = None
#     for i in range(500):
#         prv = dsa.generate_private_key(key_size)
#         params = prv.parameters().parameter_numbers()
#         if max_params is None:
#             max_params = params
#         elif params.q > max_params.q:
#             max_params = params
#         print(f'    if key_size == {key_size}:')
#         print(f'        return (')
#         print(f'            {hex(max_params.p)},')
#         print(f'            {hex(max_params.q)},')
#         print(f'            {hex(max_params.g)}')
#         print(f'        )')
#         print(f'    # {key_size} {i} {hex(max_params.q)}')


# def binsearch(curve: ec.EllipticCurve):
#     def check_num(a, curve):
#         try:
#             ec.derive_private_key(a, curve)
#             return True
#         except:
#             return False
#     max = pow(2, curve.key_size) - 1
#     min = 0
#     while min < max:
#         mid = (min + max + 1) // 2
#         if check_num(mid, curve):
#             min = mid
#         else:
#             max = mid - 1
#     return min + 1

# for (name, curve) in ec._CURVE_TYPES.items():
#     print(f'    if name == \'{name}\':\n        return {hex(binsearch(curve))}')

#0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
#0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632550

# key_size = 1024
# p = 0xC0 * pow(2, (key_size // 2) - 8)
# n_max = pow(2, key_size) - 1
# n_min = pow(2, key_size - 1)
# q_max = n_max // p
# q_min = (n_min + p - 1) // p

# print('p    ', hex(p))
# print('n_max', hex(n_max))
# print('n_min', hex(n_min))
# print('q_max', hex(q_max))
# print('q_min', hex(q_min))

# p = pow(2, (key_size // 2)) - 1
# n_max = pow(2, key_size) - 1
# n_min = pow(2, key_size - 1)
# q_max = n_max // p
# q_min = (n_min + p - 1) // p

# print('p    ', hex(p))
# print('n_max', hex(n_max))
# print('n_min', hex(n_min))
# print('q_max', hex(q_max))
# print('q_min', hex(q_min))

# print(random_bytes(1))
# print(random_bytes(17))
# print(random_bytes(32))
# print(random_bytes(512))

import json
import uuid
import zlib
import os
import time
import base64
import hashlib
import itertools
from curl_cffi import requests, CurlMime
from typing import Callable, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AwfSolver:
    def __init__(self, domain="auth.hiring.amazon.com"):
        self.domain = domain
        self.url = f'https://{domain}'
        self.endpoint = 'https://4965bc4440d4.4becc704.us-east-1.token.awswaf.com/4965bc4440d4'
        self.aesgcm = AESGCM(bytes.fromhex("6f71a512b1e035eaab53d8be73120d3fb68a0ca346b9560aab3e5cdf753d5e98"))
    
        self.CHALLENGE_SOLVERS: dict[str, Callable[..., Any]] = {
            "h72f957df656e80ba55f5d8ce2e8c7ccb59687dba3bfb273d54b08a261b2f3002": self.compute_scrypt_nonce,
            "h7b0c470f0cfe3a80a9e26526ad185f484f6817d0832712a4a37a908786a6a67f": self.hash_pow,
            "ha9faaffd31b4d5ede2a2e19d2d7fd525f66fee61911511960dcbb52d3c48ce25": self.network_bandwidth,
        }

    def encrypt(self, plaintext: bytes) -> str:
        iv = os.urandom(12)
        cipher_bytes = self.aesgcm.encrypt(iv, plaintext, None)
        tag = cipher_bytes[-16:]
        ciphertext = cipher_bytes[:-16]
        iv_b64 = base64.b64encode(iv).decode("utf-8")
        return f"{iv_b64}::{ciphertext.hex()}{tag.hex()}"

    def _fake_fingerprint(self):
        ts = int(time.time() * 1000)

        fingerprint = {
            "metrics": {
            "fp2": 2,
            "browser": 1,
            "capabilities": 2,
            "gpu": 30,
            "dnt": 0,
            "math": 1,
            "screen": 0,
            "navigator": 0,
            "auto": 0,
            "stealth": 2,
            "subtle": 0,
            "canvas": 38,
            "formdetector": 0,
            "be": 1
            },
            "start": ts,
            "flashVersion": None,
            "plugins": [
            { "name": "Chrome document Plugin", "str": "Chrome document Plugin " },
            {
                "name": "Microsoft Edge PDF Viewer",
                "str": "Microsoft Edge PDF Viewer "
            },
            { "name": "GDJEKNOP", "str": "GDJEKNOP 26140" },
            { "name": "Chromium PDF Viewer", "str": "Chromium PDF Viewer " },
            { "name": "WebKit built-in PDF", "str": "WebKit built-in PDF " },
            { "name": "PDF Viewer", "str": "PDF Viewer " },
            { "name": "Sw3jwg3", "str": "Sw3jwg3 143368" }
            ],
            "dupedPlugins": "Chrome document Plugin Microsoft Edge PDF Viewer GDJEKNOP 26140Chromium PDF Viewer WebKit built-in PDF PDF Viewer Sw3jwg3 143368||1920-1080-1080-24-*-*-*",
            "screenInfo": "1920-1080-1080-24-*-*-*",
            "referrer": "",
            "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            "location": "https://auth.hiring.amazon.com/#/login",
            "webDriver": False,
            "capabilities": {
            "css": {
                "textShadow": 1,
                "WebkitTextStroke": 1,
                "boxShadow": 1,
                "borderRadius": 1,
                "borderImage": 1,
                "opacity": 1,
                "transform": 1,
                "transition": 1
            },
            "js": {
                "audio": True,
                "geolocation": True,
                "localStorage": "supported",
                "touch": False,
                "video": True,
                "webWorker": True
            },
            "elapsed": 1
            },
            "gpu": {
            "vendor": "Brave",
            "model": "Brave",
            "extensions": [
                "ANGLE_instanced_arrays",
                "EXT_blend_minmax",
                "EXT_clip_control",
                "EXT_color_buffer_half_float",
                "EXT_depth_clamp",
                "EXT_disjoint_timer_query",
                "EXT_float_blend",
                "EXT_frag_depth",
                "EXT_polygon_offset_clamp",
                "EXT_shader_texture_lod",
                "EXT_texture_compression_bptc",
                "EXT_texture_compression_rgtc",
                "EXT_texture_filter_anisotropic",
                "EXT_texture_mirror_clamp_to_edge",
                "EXT_sRGB",
                "KHR_parallel_shader_compile",
                "OES_element_index_uint",
                "OES_fbo_render_mipmap",
                "OES_standard_derivatives",
                "OES_texture_float",
                "OES_texture_float_linear",
                "OES_texture_half_float",
                "OES_texture_half_float_linear",
                "OES_vertex_array_object",
                "WEBGL_blend_func_extended",
                "WEBGL_color_buffer_float",
                "WEBGL_compressed_texture_s3tc",
                "WEBGL_compressed_texture_s3tc_srgb",
                "WEBGL_debug_renderer_info",
                "WEBGL_debug_shaders",
                "WEBGL_depth_texture",
                "WEBGL_draw_buffers",
                "WEBGL_lose_context",
                "WEBGL_multi_draw",
                "WEBGL_polygon_mode",
                "EXT_texture_blender"
            ]
            },
            "dnt": None,
            "math": {
            "tan": "-1.4214488238747245",
            "sin": "0.8178819121159085",
            "cos": "-0.5753861119575491"
            },
            "automation": {
            "wd": { "properties": { "document": [], "window": [], "navigator": [] } },
            "phantom": { "properties": { "window": [] } }
            },
            "stealth": { "t1": 0, "t2": 0, "i": 1, "mte": 0, "mtd": False },
            "crypto": {
            "crypto": 1,
            "subtle": 1,
            "encrypt": True,
            "decrypt": True,
            "wrapKey": True,
            "unwrapKey": True,
            "sign": True,
            "verify": True,
            "digest": True,
            "deriveBits": True,
            "deriveKey": True,
            "getRandomValues": True,
            "randomUUID": True
            },
            "canvas": {
            "hash": 342310700,
            "emailHash": None,
            "histogramBins": [
                14351, 154, 41, 46, 48, 49, 27, 22, 44, 24, 37, 16, 36, 52, 31, 43, 31,
                28, 25, 31, 32, 27, 40, 28, 47, 12, 31, 32, 42, 20, 27, 35, 118, 22, 23,
                30, 22, 16, 24, 26, 27, 17, 28, 32, 15, 30, 28, 30, 32, 33, 28, 37, 30,
                17, 35, 23, 22, 25, 18, 18, 25, 25, 19, 22, 100, 16, 22, 13, 19, 19, 19,
                23, 13, 25, 12, 16, 23, 17, 14, 19, 17, 20, 17, 26, 20, 47, 15, 18, 25,
                22, 19, 18, 17, 18, 20, 23, 103, 27, 50, 38, 55, 31, 489, 31, 18, 16,
                25, 26, 18, 48, 35, 13, 20, 18, 21, 20, 28, 19, 27, 31, 19, 16, 14, 23,
                27, 12, 35, 129, 41, 36, 33, 28, 9, 14, 17, 14, 29, 30, 43, 20, 34, 24,
                26, 33, 19, 31, 64, 34, 11, 24, 14, 21, 22, 69, 18, 10, 19, 20, 22, 83,
                21, 18, 28, 6, 30, 20, 20, 24, 13, 14, 41, 19, 40, 18, 24, 24, 29, 17,
                18, 27, 15, 15, 16, 28, 11, 17, 14, 23, 20, 15, 19, 99, 14, 10, 18, 16,
                15, 20, 31, 13, 29, 34, 27, 48, 55, 48, 34, 46, 31, 45, 42, 13, 28, 21,
                26, 25, 30, 25, 16, 22, 22, 26, 26, 113, 41, 30, 16, 21, 25, 15, 28, 35,
                22, 33, 24, 60, 27, 34, 26, 36, 46, 32, 32, 28, 19, 51, 33, 50, 31, 44,
                41, 54, 77, 56, 123, 13586
            ]
            },
            "formDetected": False,
            "numForms": 0,
            "numFormElements": 0,
            "be": { "si": False },
            "end": ts + 2,
            "errors": [],
            "version": "2.4.0",
            "id": str(uuid.uuid4())
        }

        payload = json.dumps(fingerprint, separators=(",", ":")).encode()
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        hex_crc = f"{crc:08x}"
        checksum = hex_crc.encode("ascii").upper()
        data = checksum + b"#" + payload
        return checksum, self.encrypt(data)

    def _build_payload(self, inputs):
        checksum, fp = self._fake_fingerprint()
        checksum = checksum.decode()
        return {
            # 'solution_metadata': {"challenge": inputs['challenge'], "solution":None,"signals":[{"name":"Zoey","value":{"Present":"hXMT8ZW6Jve+8BQp::2aae8ef38648e0c8d36623d13b1d02fa52b9cb47d121b72994529d0ff4bdd90a338d9504f0b70f1a71b4dfbba996e7d28d3afe6a93300b1d51ad5009659309373e854c73f3303fdf43c20587086d3fa7991ab860cf9707dbc8ecd590c25503ad7c80783bf0362e3d4d48f12e0a603de8cffec98162adc15c3576564455772a7c93891de84831d13fae3679e7bbaf97db6ad8f146d47825ece286038e47657569cc669baeb7efc52b7a030604527ca45d21286d0ee7a8b3b974d6c0811539fb76bb98e9402a9fda7a77aa9eb1ab8a0d7c6c964e7d5aa5a00fbdf6f69385aba1840125391893dff551b8a38f237d2d64fd8332371a66696d104bc8fc5be476574dea9f465f0f3bc428faa354e41e2f12a21b6df3a753462db94fae774cf4c280d3445b782b9ff10eecb3e380fce8ba78bca726ac044730c3892f6ecef3d70be3bbccab0c859413ff8bb22f82962800a785cfc17d3cf3f6a51a93acf541a567e26ee19fedd667d679f1b66feadd276d0e3e3e0163036abae474d55b27b19987b575720a2c1aefeddedcdf000c82ed0ae51902361aabf6502f287b3bd8317dc0041d71e1cfe57dd3ecb7f19278a3d16572b817f0e955118b08dd913de1b84d6abe99e1322bd6d598693b46b15dcb4783148f2efc1a9de985b3768eba5b53410e4eba873f1d0e2f1977e7409e9e895b22341cffb0e4c8347324bbc513aef179a3e0a1ed139d6a7158b739e8f0ae0b6906b239b1ba44f1b06b8dcd086400651a60a7e893e1195d60f3e2e653b4195f97112241369eb5b6dc360ac7f9cc15f3d568409a3ded96fee4d07b507382b6e85e7f4da8afd3bafdc57c0510d40d868b6fa3677ea2ee5d8b4bb1361438c47bdb4a8e4dc48029961977214e768c11bad13518bcc62f6ec794f7742a2a3ecb0414e147404822e209d34364d6d87f3bb4a8ba65690a5ad5c76556196132a031972cbcac7d76eaa0fbed4ff821c0f22aac51ec56b836ecf323fde60ccea70f03b40e7517a52c50217769fd9ee9f216c9f0427f7890e8b7b201d665cac48e7c1b469b0f365534b8bc9a6f5e50f3be761a6010dfc6c1280668c8d0054ffa0252c210b112846f6d27fc09def35facbddee7b95c5a635adee84724af9f7939e258451bc8c625e637a12ddef3df08d957371ea02fe09d46a6b60af898864f30a050235d57f7340c37cc0de31d0b0b5f3b07fb52c2ded9c4096e65e44e763394a44309aaaa96e6a02ca625451661a8ab6b6cec98f0da9667983d26f3cfa49d44e4e1cf7fbff7d97cb8ed34e476549471abfb7d64a713f60ba5aff37d68aa8902c921633bbcfb043ab18e72e18bd21183d75f227e37f547159b3b242f30006729b71235c1d5c00d9d2230d4a58d54643fea9106fec1ba795fd4d3760e6bca3c90ab5b727572fe047ff1c6cf56689fb2fc7058afa08b9bb92bc16bd41454ff42896b62552074c399c45fbfbd1cf55a5cdcbb188ced7fc5d61fd652a5864d00b1104c351bc50e9bfe4c3b708574dd051ad7db9420d5519f35588a95d0f5fe738b3cecee1617c30ad3a03e031967152dfafb66d4ad35884f366f570a3e7bdd5479633bab0240691e98c7922a80606fdf75e474713d3fafcf29a82c98346a32de4a360930a12dc0a31acca5d5b879ee3b6383c99a3ac4c0de56b0db72f8d3f5fe46a6d4da951f9f61698b70e2d355a79c7846c6108d3293597b4984d2e95b3a38c1db9e00cbc30b1037902a3005cd172d9491c407a935a8dcc4305bb1710ae578dba9b86162d6d77526fb99012f6e131a8259d7b1bf2758f35be08c48848e1a9603b08fe599f5e69d13f0648333c1d3ab068f111d023cd14c006948883b03c5dab5f601af7f1a6c24833d7bdada147f43076b9c0f0cfcfb0cc089b57c700df5fa6f163b56169c96578efee5a8a0005efeaf6ddda9f5ec9110ba48deed95d49cb12ba1cfd4137f578176df2507f3aa0896362569ce38c8c6ecc1882e405d17df16b850d69768545147e477a5f2556dfcc5bdbf2d41453bee6b952336c3d9a5925df1d4528b3d8d5d63a58a3f9cc8e86008e59597b6a69bc156ec89dfd4abcfe34f7acf7715f1c696f00bb1438393fb52f5deeaeba8afdbe39eba18af470621bbf17007a9bda1b058410f207e328fbe0fc559481dc892dc2d2b66944c8b7468e7b54c41afdfb2d8ca978e820673e093cd12ccbaa08d8333c89075a3c5e5421a62977f947a47fa7eb90a2f53d086eb8dfbf6624ee6d86b284784213d3f7d4cfb57bd3b73d2a9de1180a3a1e3cdf40220a982220ad0e0afc9f59c6f0ab2a7e8f9658aa2154645a89bd89f314203b5218e729150dce6eebc7828abaaec6cd6b95c05ee3abf3bca335a1e243403e9bf27c07ab353c0b178e2009b5cbc89e76c75c7e1e903198b475e3115b61d3ab7462db332eb3ad08ed6b3a92910d0b2ce99ad3a77ecd2da643d6f6e70f5deeb8d877f44b87fc0e7a34a046cf48be41c61a724933e787915ed9548db7884ffa94475c590e50dcf0c9891c58d6a8fd25d805b5ace8712049d67e227102f28858ce2adeed4704dcd7c83083af71fda2e5fcc240a9e255119b5e77b1da02890de0197c4f5ba8d90a234ae45cfc4a2a6f2297814fd1da542a96e293cfc3cd19316f0467a834a7dcb10869e981b8e4bd409b0771fbe0933abf3789a6704cb3c2d7d2819b8f02b7c36e6bff75878b5b9bcacc4207bac3e4782133fb504857af1bf8328b1af5042482d6f12dc5e557b623e415d5d7fa6c511fdf06c0ca78d359cd8fe7927f36f414c118f62a92f90458f2e8fb105f91b0f80e209e8d9660f8e6d7fbf1cd05ecba5646634dda1b055955a13bc0eae66a7501e17a46fef00822a8675cbf41cf6d40a3cb072ed46a096811d759b96c8ce0b3582463b9e8c6f5ac606e61cd08b828eea3ee7356dd91c56f8f18847b2680b8b33d5d462c12b493ad7dfbcac281848fdf594d5c602dcca308e9a719b2a3a467faa4a8b436f20848efd9e25e04ce67f0430289a1df2c485ddb58b7cc8bc380fd8d78756659ec884a4199947f1e9f50ac0f6c30c340e1ce58e42557804788e01ca9ccb6021aba3812ee894ea01eb58d1423fabd9fd919c91349a98ca36e40b04715497870bd1c0d95866cf0df994ecdbc59564b8d420a9a7fb7029f35abc7c817e4404b6cab1428037a7bee68e49d3a77e1afd14a83d220f45cf9db834ac1498fed3edd574c73c64c8416d47caefb96a236f6e528d0512c2b85f7c1edd70e1be5372788791f22f562aa4f756eb3603e03d95b0e6ee15f24e68397cf702cdaef66fb3490873aacfecf014b818e5e98e9126ae649af93841c9ed696433d4c3fdfa50b1b06d8b04b7c4f108ff88ddd4b5507095284a675175b4f1286bb737c5e15a6313093f34f041d942b43efdcd6acb185e8fef58955f2c46aa208c678bee765632f2bd5262db23b9cd06606c0f88536c9e870abd51556d7d2e6ccaabd62b32e78eac4338401c8867ab0f54ce0e7f467d3974053e7154c23644a1cac8746cc30ce725ee894626a89607de826fb1880dee4326b730ac11bb39b2a8db21054c26804da69a8b5424014e30789e934d6c6c6f341befba5bd88ab92baeaf460c9422f8f0d21024e97ad6bcbe0aee8794e399dd3d111e7abbf19670764f093d2719135a395f4da471aaf8f455f57c246937c13edaf8676d8830a877412ab4bf8204cf1217806f96af770cea12577fc138c2dd361ad429764306f745c87ca1a5167ff5ab1da6e9460469e67d47f1cb03f7bfe6f130a04855cc34035f0ea4ed999b1ae942eb7c28be047773df45f6b55b989a629580027cab5f06fcbbceab756297696f85bd56783cdeeaa0e21e7879bbdc3297c8cbd759eba6bcc5d1e960098097ed0157226a795cf70a66674265ba0dbfef9462b2a7dfaedf75843d08f1e8b7648afe59c5e9cf7608ba2491746f06dfd3e66299fcae2e4b1019624bfdf8ada5264d4a7069d279678cf1a10fac4f79222b934bf1cb0b5be6765f445409aa8181ce21a4e545fc3aa1fc35d2de5c6f6fa5d6b179f0540f563e494e1eb80a257450c9ccb7320f12d2dcc846d5c482cca060d58f4bbbb543eb453d46056c1e3b77f47e7bb86b1bc1311d6d07900c661872785847ff29ecd41876077bedbc503086bda661538ba5acb52063ec3262e4acd33a9a25591e9e475d69ec93358918524ddefe0f7c24aeb1959b0b865ec5c4d812de3f424a3c6cbdcfa2cbdfff4755c093487ce00d87c6fc4c42169699e436dc612cca8c078a61059dbc3e50e2b2128bac74ecc723ad0e65f851604c4f91695abdb5249db6d0fd1919a3c65c444bd9f1e393e455f83ea9f8a86aedbb8044293a5baf417781185ddd8c03632306e485d17b1e11928ca8234fb8641cb170e715d5b2f20a835d96fe56a126c7b86e95919f52b1410e413109a8b5957a0cc7d10eea5cacd807a0d9799246ffc7e676bc3c3f6ac2387d5f5c9dac1105963f1a7afaead84c80df03a0aa2d4505f62feb2fac9f8e678176f860b6dc1b2b0e904ff90fc1147a409690dcda505731fdb777baa1b06971a767479d0caffd4beedea55d0b7d90ffbac8d647f98467413dd614c4c686db5d48958a44a5299d44448da02420d9d067f4f55ede28aa9907b2d9891c7c5f0ea00d61fc85f14d7496a60c3146223acf79a230e16571cb6e36fb33696a5eb1c09d9a858c5b2b988740031eccef7e885453618d3a5157d4a08f1ee7296560ae0c1be98dc619941d6e0a1f6be2dc1a8d42efbb526df5990da965cc073da4c751be5393dc28f7af02d7840420c69f71ae87959725fab76a8729682ea6e79bc593f8deff9b3abf5e142161427f749dca7d90ed3ee78c0bd9b99a82f3c53bf0ec329c2bfc014a08a0d9262a3086cf282fc4e66d2ae5b52620a72f9bba98afd3253c04bb0be9f7deb13115d86de57d2542217845c9c7dc980668ea7ce00cee6012ecc2651d4f2143d53d9430e85a529330151f5704fcabc045a175ccc45f76206f2d8c7e2ecf9f9e946ffd1948b1a9ae203b93acb08578e1ab216783b03249f753677b942dfca89fa253975ab433c0e7d8cc9827620862f5be1c723ff49212d98177415c2fed2603541c1ac62d91529dcea174ff3017beed2618213a26a02fc0f97974a2a6f50ab16c5e48011791f5bc8bdbdde21a270cdb70b32159ada41ff7d04961c2c6a3341eab5d8e937a872e81b24f78fcc91dae09a6cd82304aa8e588aefe228a6852f5bae6d7d9319dba1e3111a9a7fb26507a1485ebb73126f25ae1326aeff1913f6685be541c852ed499c55e415c09efb57150dd9be1"}}],"checksum":"805BE9E8","existing_token":None,"client":"Browser","domain":"auth.hiring.amazon.com","metrics":[{"name":"2","value":1.1000000000931323,"unit":"2"},{"name":"100","value":2,"unit":"2"},{"name":"101","value":1,"unit":"2"},{"name":"102","value":2,"unit":"2"},{"name":"103","value":30,"unit":"2"},{"name":"104","value":0,"unit":"2"},{"name":"105","value":1,"unit":"2"},{"name":"106","value":0,"unit":"2"},{"name":"107","value":0,"unit":"2"},{"name":"108","value":0,"unit":"2"},{"name":"undefined","value":2,"unit":"2"},{"name":"110","value":0,"unit":"2"},{"name":"111","value":38,"unit":"2"},{"name":"112","value":0,"unit":"2"},{"name":"undefined","value":1,"unit":"2"},{"name":"3","value":2.5,"unit":"2"},{"name":"7","value":0,"unit":"4"},{"name":"1","value":90.90000000002328,"unit":"2"},{"name":"4","value":5.299999999930151,"unit":"2"},{"name":"5","value":0.5999999999767169,"unit":"2"},{"name":"6","value":96.79999999993015,"unit":"2"},{"name":"8","value":1,"unit":"4"}]},
            "solution_metadata": {"challenge": inputs['challenge'], "solution":None,"signals":[{"name":"Zoey","value":{"Present": fp}}],"checksum":checksum,"existing_token":None,"client":"Browser","domain":"auth.hiring.amazon.com","metrics":[{"name":"2","value":1.1000000000931323,"unit":"2"},{"name":"100","value":2,"unit":"2"},{"name":"101","value":1,"unit":"2"},{"name":"102","value":2,"unit":"2"},{"name":"103","value":30,"unit":"2"},{"name":"104","value":0,"unit":"2"},{"name":"105","value":1,"unit":"2"},{"name":"106","value":0,"unit":"2"},{"name":"107","value":0,"unit":"2"},{"name":"108","value":0,"unit":"2"},{"name":"undefined","value":2,"unit":"2"},{"name":"110","value":0,"unit":"2"},{"name":"111","value":38,"unit":"2"},{"name":"112","value":0,"unit":"2"},{"name":"undefined","value":1,"unit":"2"},{"name":"3","value":2.5,"unit":"2"},{"name":"7","value":0,"unit":"4"},{"name":"1","value":90.90000000002328,"unit":"2"},{"name":"4","value":5.299999999930151,"unit":"2"},{"name":"5","value":0.5999999999767169,"unit":"2"},{"name":"6","value":96.79999999993015,"unit":"2"},{"name":"8","value":1,"unit":"4"}]},
            "solution_data": b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==',
        }

    def _check_digest_difficulty(self, digest: bytes, difficulty: int) -> bool:
        full, rem = divmod(difficulty, 8)
        if digest[:full] != b"\x00" * full:
            return False
        if rem and (digest[full] >> (8 - rem)):
            return False
        return True

    # SOLVERS
    def network_bandwidth(self, challenge: str, salt: str, difficulty: int) -> str:
        _DEFAULT_BANDWIDTH_SIZES = {1: 0x400, 2: 0xA * 0x400, 3: 0x64 * 0x400, 4: 0x100000, 5: 0xA * 0x100000}
        return base64.b64encode(b"\x00" * _DEFAULT_BANDWIDTH_SIZES.get(difficulty))

    def hash_pow(self, challenge: str, salt: str, difficulty: int) -> Optional[str]:
        prefix = (challenge + salt).encode()
        for nonce in itertools.count():
            digest = hashlib.sha256(prefix + str(nonce).encode()).digest()
            if self._check_digest_difficulty(digest, difficulty):
                return str(nonce)
        return None

    def compute_scrypt_nonce(
        self,
        challenge: str,
        salt: str,
        difficulty: int,
        n: int = 128,
        r: int = 8,
        p: int = 1,
        dklen: int = 16,
    ) -> Optional[str]:
        prefix = challenge + salt
        for nonce in itertools.count():
            digest = hashlib.scrypt(
                password=f"{prefix}{nonce}".encode(),
                salt=salt.encode(),
                n=n,
                r=r,
                p=p,
                dklen=dklen,
            )
            if self._check_digest_difficulty(digest, difficulty):
                return str(nonce)
        return None

    def __call__(self):
        inputs = requests.get(f'{self.endpoint}/inputs', params={'client': 'browser'}).json()
        payload = self._build_payload(inputs)

        multipart = CurlMime()
        multipart.addpart(
            name="solution_metadata",
            data=json.dumps(
                payload["solution_metadata"],
                separators=(",", ":")
            ).encode(),
        )

        multipart.addpart(
            name="solution_data",
            data=payload["solution_data"],
        )
        challege_response = requests.post(f'{self.endpoint}/mp_verify',multipart=multipart, headers={
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-GB,en;q=0.6",
                "cache-control": "no-cache",
                "origin": "https://auth.hiring.amazon.com",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://auth.hiring.amazon.com/",
                "sec-ch-ua": '"Not=A?Brand";v="99", "Brave";v="151", "Chromium";v="151"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Linux"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                "sec-gpc": "1",
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            },
        ).json()

        return challege_response['token']

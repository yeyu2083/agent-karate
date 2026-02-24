function fn() {
    // Obtener el ambiente (dev, qa, prod) o usar 'dev' por defecto
    var env = karate.env || 'dev';
    karate.log('Ambiente configurado:', env);

    // Configuración base
    var config = {
        env: env,
        // URLs base para diferentes ambientes
        baseUrl: 'https://jsonplaceholder.typicode.com',
        apiUrl: 'https://jsonplaceholder.typicode.com',
        timeout: 10000, // timeout en milisegundos

        // Headers que imitan un navegador real (anti-Cloudflare)
        commonHeaders: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
    };

    // Configuración específica por ambiente
    if (env === 'dev') {
        config.baseUrl = 'https://jsonplaceholder.typicode.com';
        config.apiUrl = 'https://reqres.in/api';
    } else if (env === 'qa') {
        config.baseUrl = 'https://qa.jsonplaceholder.typicode.com';
        config.apiUrl = 'https://qa.reqres.in/api';
    } else if (env === 'prod') {
        config.baseUrl = 'https://jsonplaceholder.typicode.com';
        config.apiUrl = 'https://reqres.in/api';
    }

    // Funciones útiles globales
    config.generateRandomEmail = function () {
        var timestamp = new Date().getTime();
        return 'user' + timestamp + '@test.com';
    };

    config.generateRandomString = function (length) {
        var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var result = '';
        for (var i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    };

    // Configurar retry automático con delay entre intentos
    karate.configure('retry', { count: 3, interval: 2000 });

    // Configurar timeout de conexión
    karate.configure('connectTimeout', config.timeout);
    karate.configure('readTimeout', config.timeout);

    // ✅ ANTI-CLOUDFLARE: Habilitar soporte para cookies y sesiones
    karate.configure('ssl', false); // Permitir SSL sin validación (si es necesario)
    
    // Función para agregar delay entre peticiones
    config.delay = function(ms) {
        var start = new Date().getTime();
        while (new Date().getTime() - start < ms) {
            // Esperar
        }
    };

    return config;
}

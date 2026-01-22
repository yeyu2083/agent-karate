function fn() {
    // Obtener el ambiente (dev, qa, prod) o usar 'dev' por defecto
    var env = karate.env || 'dev';
    karate.log('Ambiente configurado:', env);

    // Configuración base
    var config = {
        env: env,
        // URLs base para diferentes ambientes
        baseUrl: 'https://jsonplaceholder.typicode.com',
        apiUrl: 'https://reqres.in/api',
        timeout: 10000, // timeout en milisegundos

        // Headers comunes
        commonHeaders: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
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

    // Configurar retry automático
    karate.configure('retry', { count: 3, interval: 2000 });

    // Configurar timeout de conexión
    karate.configure('connectTimeout', config.timeout);
    karate.configure('readTimeout', config.timeout);

    return config;
}

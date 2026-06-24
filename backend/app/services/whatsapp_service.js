const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const BACKEND_URL = 'http://127.0.0.1:8000';

let BOT_READY_AT = null;
const processedMessages = new Set();

const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './.wwebjs_auth'
    }),
    puppeteer: {
        headless: false,
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

function normalizeSenderId(from) {
    return from
        .replace('@c.us', '')
        .replace('@lid', '')
        .trim();
}

client.on('qr', (qr) => {
    console.log('\nEscanea este QR con WhatsApp:\n');
    qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
    console.log('WhatsApp autenticado correctamente');
});

client.on('ready', () => {
    BOT_READY_AT = Date.now();

    console.log('\nBot conectado a WhatsApp');
    console.log('Esperando mensajes privados nuevos...\n');
});

client.on('auth_failure', (message) => {
    console.error('Fallo de autenticación:', message);
});

client.on('disconnected', (reason) => {
    console.log('WhatsApp desconectado:', reason);
    BOT_READY_AT = null;
});

client.on('message', async (msg) => {
    try {
        if (!BOT_READY_AT) return;

        if (msg.fromMe) return;

        if (msg.from === 'status@broadcast') return;

        if (msg.from.includes('@g.us')) return;
        if (msg.to && msg.to.includes('@g.us')) return;

        if (!msg.body || msg.body.trim() === '') return;

        const messageId = msg.id && msg.id._serialized
            ? msg.id._serialized
            : `${msg.from}-${msg.timestamp}-${msg.body}`;

        if (processedMessages.has(messageId)) {
            return;
        }

        processedMessages.add(messageId);

        const messageTimeMs = msg.timestamp * 1000;

        if (messageTimeMs < BOT_READY_AT) {
            console.log('\nMensaje viejo ignorado');
            console.log('from:', msg.from);
            console.log('mensaje:', msg.body);
            return;
        }

        const numero = normalizeSenderId(msg.from);
        const mensaje = msg.body.trim();

        console.log('\nMENSAJE PRIVADO NUEVO RECIBIDO');
        console.log('from:', msg.from);
        console.log('numero normalizado:', numero);
        console.log('mensaje:', mensaje);

        const response = await axios.post(
            `${BACKEND_URL}/chat`,
            {
                numero: numero,
                mensaje: mensaje
            },
            {
                timeout: 120000
            }
        );

        const respuesta = response.data.respuesta;

        console.log('Respuesta enviada:\n' + respuesta);

        await msg.reply(respuesta);

    } catch (error) {
        console.error('Error al procesar mensaje:', error.message);

        if (error.response) {
            console.error('Backend respondió:', error.response.data);
        }

        try {
            await msg.reply(
                'Error al procesar tu mensaje. Verifica que el backend esté encendido.'
            );
        } catch (replyError) {
            console.error('No se pudo responder:', replyError.message);
        }
    }
});

console.log('Iniciando bot de alacena inteligente...');
console.log('Cargando WhatsApp Web...\n');

client.initialize();
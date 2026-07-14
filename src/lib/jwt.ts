import crypto from 'crypto';

const JWT_SECRET = process.env.JWT_SECRET || "firestorm_chess_secure_fallback_secret_key_2026";

export function generateSessionToken(uid: string, email: string) {
    const payload = JSON.stringify({ uid, email, exp: Date.now() + 30 * 24 * 60 * 60 * 1000 });
    const payloadB64 = Buffer.from(payload).toString('base64');
    const signature = crypto.createHmac('sha256', JWT_SECRET).update(payloadB64).digest('hex');
    return `${payloadB64}.${signature}`;
}

export function verifySessionToken(token: string) {
    try {
        const parts = token.split('.');
        if (parts.length !== 2) return null;
        const [payloadB64, signature] = parts;
        const expectedSignature = crypto.createHmac('sha256', JWT_SECRET).update(payloadB64).digest('hex');
        if (signature !== expectedSignature) return null;
        const payloadStr = Buffer.from(payloadB64, 'base64').toString('utf8');
        const payload = JSON.parse(payloadStr);
        if (payload.exp < Date.now()) return null;
        return payload; // { uid, email }
    } catch (e) {
        return null;
    }
}

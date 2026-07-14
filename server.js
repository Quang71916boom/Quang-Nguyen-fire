import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { GoogleGenAI, ThinkingLevel } from '@google/genai';
import dotenv from 'dotenv';
import crypto from 'crypto';
import { db } from './src/db/index.ts';
import { rlMemory, gameHistory, users } from './src/db/schema.ts';
import { requireAuth } from './src/middleware/auth.ts';
import { eq } from 'drizzle-orm';
import { getOrCreateUser } from './src/db/users.ts';
import { adminAuth } from './src/lib/firebase-admin.ts';
import { generateSessionToken } from './src/lib/jwt.ts';

// Load local .env variables
dotenv.config();

const currentDir = typeof __dirname !== 'undefined' ? __dirname : process.cwd();

const app = express();
const PORT = 3000;

app.use(express.json());

// Set up Google Gen AI with lazy loading
let ai = null;
function getAI() {
    if (!ai) {
        const apiKey = process.env.GEMINI_API_KEY;
        if (apiKey) {
            ai = new GoogleGenAI({
                apiKey: apiKey,
                httpOptions: {
                    headers: {
                        'User-Agent': 'aistudio-build'
                    }
                }
            });
        }
    }
    return ai;
}

app.post('/api/history', requireAuth, async (req, res) => {
    try {
        const userRecord = await getOrCreateUser(req.user.uid, req.user.email);
        await db.insert(gameHistory).values({
            userId: userRecord.id,
            historyData: req.body
        });
        res.json({ success: true });
    } catch (e) {
        res.status(500).json({ error: String(e) });
    }
});

app.get('/api/history', requireAuth, async (req, res) => {
    try {
        const userRecord = await getOrCreateUser(req.user.uid, req.user.email);
        const result = await db.select().from(gameHistory).where(eq(gameHistory.userId, userRecord.id));
        if (result.length > 0) {
            res.json(result.map(r => r.historyData).flat());
        } else {
            res.json([]);
        }
    } catch (e) {
        res.status(500).json({ error: String(e) });
    }
});

app.post('/api/rl_memory', requireAuth, async (req, res) => {
    try {
        const userRecord = await getOrCreateUser(req.user.uid, req.user.email);
        await db.insert(rlMemory).values({
            userId: userRecord.id,
            gamesPlayed: req.body.games_played || 0,
            botWins: req.body.bot_wins || 0,
            botLosses: req.body.bot_losses || 0,
            botDraws: req.body.bot_draws || 0,
            qTable: req.body.q_table || {},
            recentLearnings: req.body.recent_learnings || []
        }).onConflictDoUpdate({
            target: rlMemory.userId,
            set: {
                gamesPlayed: req.body.games_played,
                botWins: req.body.bot_wins,
                botLosses: req.body.bot_losses,
                botDraws: req.body.bot_draws,
                qTable: req.body.q_table,
                recentLearnings: req.body.recent_learnings,
                updatedAt: new Date()
            }
        });
        res.json({ success: true });
    } catch (e) {
        res.status(500).json({ error: String(e) });
    }
});

app.get('/api/rl_memory', requireAuth, async (req, res) => {
    try {
        const userRecord = await getOrCreateUser(req.user.uid, req.user.email);
        const result = await db.select().from(rlMemory).where(eq(rlMemory.userId, userRecord.id));
        if (result.length > 0) {
            const row = result[0];
            res.json({
                games_played: row.gamesPlayed,
                bot_wins: row.botWins,
                bot_losses: row.botLosses,
                bot_draws: row.botDraws,
                q_table: row.qTable,
                recent_learnings: row.recentLearnings
            });
        } else {
            const defaultRl = {
                games_played: 0,
                bot_wins: 0,
                bot_losses: 0,
                bot_draws: 0,
                q_table: {},
                recent_learnings: []
            };
            res.json(defaultRl);
        }
    } catch (e) {
        res.status(500).json({ error: String(e) });
    }
});

app.post('/api/bot_move', async (req, res) => {
    try {
        const pythonPort = process.env.PYTHON_PORT || 3001;
        const response = await fetch(`http://127.0.0.1:${pythonPort}/api/bot_move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        });
        const data = await response.json();
        res.json(data);
    } catch (e) {
        // Fallback to Pyodide client-side engine if Python backend is unavailable
        console.error("Python engine not reachable", e);
        res.json({ best_move: null, eval_score: 0.0 });
    }
});

app.post('/api/support', async (req, res) => {
    const aiClient = getAI();
    if (!aiClient) {
        return res.status(400).json({ error: "GEMINI_API_KEY environment variable is not configured. Please set it in Settings > Secrets." });
    }
    
    try {
        const messages = req.body.messages || [];
        const contents = [];
        
        for (const msg of messages) {
            let role = msg.role;
            if (role === 'assistant') role = 'model';
            
            if (contents.length > 0 && contents[contents.length - 1].role === role) {
                contents[contents.length - 1].parts[0].text += "\\n\\n" + (msg.content || "");
            } else {
                contents.push({
                    role: role,
                    parts: [{ text: msg.content || "" }]
                });
            }
        }
        
        const systemInstruction = `You are a professional customer support assistant and technical troubleshooter for Firestorm Chess.
Firestorm Chess is a state-of-the-art hybrid chess application built with custom local Python WebAssembly (Pyodide) and a threaded Python backend engine (server_engine.py).
It features real-time move analysis, reinforcement learning (RL) backpropagation on a local Q-table (saved locally and to Firestore), offline gameplay vs. various minimax personalities (Beginner Beth 1000, Coach Nakamura 1600, GM Garry 2000, and FireStorm GM Alpha 2400), automatic opening book detection, and calendar events.

Provide extremely helpful, friendly, and accurate troubleshooting advice. Address questions about performance, the engine, RL learning mechanics, saving history to Firebase, or rules of the game. Keep formatting neat and clear, using Markdown where appropriate.

IMPORTANT: To save API tokens, you MUST strictly refuse to answer any questions or engage in conversations that are not related to Firestorm Chess, the app itself, or the game of chess. If the user asks something unrelated, briefly apologize and explain that you can only answer questions related to the app or chess.`;
        
        const highThinking = req.body.highThinking === true;
        const modelToUse = highThinking ? 'gemini-3.5-flash' : 'gemini-3.1-flash-lite';
        
        const config = {
            systemInstruction: systemInstruction
        };
        
        if (highThinking) {
            config.thinkingConfig = {
                thinkingBudget: 1024 // 1024, 2048, or 4096 is a good thinking budget for Gemini 3.5 Flash
            };
        }
        
        const response = await aiClient.models.generateContent({
            model: modelToUse,
            contents: contents,
            config: config
        });
        
        res.json({ reply: response.text });
        
    } catch (e) {
        res.status(500).json({ error: String(e) });
    }
});

// --- Custom Token-Based Secure Cryptographic/Passkey Authentication Gateways ---

// Register Cryptographic Account
app.post('/api/auth/register-crypto', async (req, res) => {
    const { email, pseudonymEmail, derivedPass } = req.body;
    if (!email || !pseudonymEmail || !derivedPass) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    try {
        // Check if user already exists in Drizzle DB
        const existingUsers = await db.select().from(users).where(eq(users.uid, pseudonymEmail));
        if (existingUsers.length > 0) {
            return res.status(400).json({ error: 'email-already-in-use' });
        }

        const derivedPassHash = crypto.createHash('sha256').update(derivedPass).digest('hex');

        // Create user in our PG DB
        await db.insert(users).values({
            uid: pseudonymEmail,
            email: pseudonymEmail,
            passwordHash: derivedPassHash,
            realEmail: email
        });

        // Generate our custom JWT-equivalent token
        const customToken = generateSessionToken(pseudonymEmail, email);
        res.json({ success: true, customToken });
    } catch (e) {
        console.error("Register Crypt error:", e);
        res.status(500).json({ error: String(e.message || e) });
    }
});

// Login Cryptographic Account
app.post('/api/auth/login-crypto', async (req, res) => {
    const { email, pseudonymEmail, derivedPass } = req.body;
    if (!email || !pseudonymEmail || !derivedPass) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    try {
        // Retrieve user from our Drizzle DB
        const existingUsers = await db.select().from(users).where(eq(users.uid, pseudonymEmail));
        if (existingUsers.length === 0) {
            return res.status(401).json({ error: 'user-not-found' });
        }

        const user = existingUsers[0];
        const storedHash = user.passwordHash;

        const currentHash = crypto.createHash('sha256').update(derivedPass).digest('hex');

        if (!storedHash || storedHash !== currentHash) {
            return res.status(401).json({ error: 'invalid-credential' });
        }

        // Generate our custom JWT-equivalent token
        const customToken = generateSessionToken(pseudonymEmail, user.realEmail || email);
        res.json({ success: true, customToken });
    } catch (e) {
        console.error("Login Crypt error:", e);
        res.status(500).json({ error: String(e.message || e) });
    }
});

// Register Passkey
app.post('/api/auth/register-passkey', async (req, res) => {
    const { email, pseudonymEmail, derivedPassword } = req.body;
    if (!email || !pseudonymEmail || !derivedPassword) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    try {
        // Check if user already exists in Drizzle DB
        const existingUsers = await db.select().from(users).where(eq(users.uid, pseudonymEmail));
        if (existingUsers.length > 0) {
            return res.status(400).json({ error: 'email-already-in-use' });
        }

        const derivedPassHash = crypto.createHash('sha256').update(derivedPassword).digest('hex');

        // Create user in our PG DB
        await db.insert(users).values({
            uid: pseudonymEmail,
            email: pseudonymEmail,
            passwordHash: derivedPassHash,
            realEmail: email
        });

        // Generate our custom JWT-equivalent token
        const customToken = generateSessionToken(pseudonymEmail, email);
        res.json({ success: true, customToken });
    } catch (e) {
        console.error("Register Passkey error:", e);
        res.status(500).json({ error: String(e.message || e) });
    }
});

// Login Passkey
app.post('/api/auth/login-passkey', async (req, res) => {
    const { email, pseudonymEmail, derivedPassword } = req.body;
    if (!pseudonymEmail || !derivedPassword) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    try {
        // Retrieve user from our Drizzle DB
        const existingUsers = await db.select().from(users).where(eq(users.uid, pseudonymEmail));
        if (existingUsers.length === 0) {
            return res.status(401).json({ error: 'user-not-found' });
        }

        const user = existingUsers[0];
        const storedHash = user.passwordHash;

        const currentHash = crypto.createHash('sha256').update(derivedPassword).digest('hex');

        if (!storedHash || storedHash !== currentHash) {
            return res.status(401).json({ error: 'invalid-credential' });
        }

        // Generate our custom JWT-equivalent token
        const customToken = generateSessionToken(pseudonymEmail, user.realEmail || email);
        res.json({ success: true, customToken });
    } catch (e) {
        console.error("Login Passkey error:", e);
        res.status(500).json({ error: String(e.message || e) });
    }
});

// Delete Passkey completely from DB & Firebase
app.post('/api/auth/delete-passkey', async (req, res) => {
    const { pseudonymEmail } = req.body;
    if (!pseudonymEmail) {
        return res.status(400).json({ error: 'Missing pseudonymEmail' });
    }

    try {
        // Retrieve user from our Drizzle DB
        const existingUsers = await db.select().from(users).where(eq(users.uid, pseudonymEmail));
        if (existingUsers.length > 0) {
            const user = existingUsers[0];
            
            // Delete related tables first due to foreign keys
            await db.delete(rlMemory).where(eq(rlMemory.userId, user.id));
            await db.delete(gameHistory).where(eq(gameHistory.userId, user.id));
            
            // Finally delete the user
            await db.delete(users).where(eq(users.id, user.id));
            console.log(`Successfully deleted user with uid/pseudonymEmail: ${pseudonymEmail} and all matching history/RL tables.`);
        }

        // Try to delete from Firebase auth if user exists with that uid
        try {
            await adminAuth.deleteUser(pseudonymEmail);
            console.log(`Successfully deleted user from Firebase Auth: ${pseudonymEmail}`);
        } catch (firebaseErr) {
            // It might not exist in Firebase Auth, ignore
            console.log("Firebase Auth delete ignored (might not exist):", firebaseErr.message);
        }

        res.json({ success: true });
    } catch (e) {
        console.error("Delete passkey error:", e);
        res.status(500).json({ error: String(e.message || e) });
    }
});

// Serve static files from root in dev, dist in prod
// Wait, the build script copies to dist/. Let's serve everything statically.
app.use(express.static(currentDir));

app.get('*', (req, res) => {
    res.sendFile(path.join(currentDir, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Node server running on port ${PORT}`);
});

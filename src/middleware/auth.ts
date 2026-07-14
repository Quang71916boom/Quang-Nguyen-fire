import { adminAuth } from '../lib/firebase-admin.ts';
import { verifySessionToken } from '../lib/jwt.ts';

export const requireAuth = async (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized: Missing token' });
  }

  const token = authHeader.split('Bearer ')[1];

  // Try local secure token verification first
  const localUser = verifySessionToken(token);
  if (localUser) {
    req.user = {
      uid: localUser.uid,
      email: localUser.email,
    };
    return next();
  }

  try {
    const decodedToken = await adminAuth.verifyIdToken(token);
    req.user = decodedToken;
    next();
  } catch (error) {
    console.error('Error verifying Firebase ID token:', error);
    return res.status(401).json({ error: 'Unauthorized: Invalid token' });
  }
};

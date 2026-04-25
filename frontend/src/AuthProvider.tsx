import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { onAuthStateChanged, signInWithPopup, signOut, GoogleAuthProvider } from 'firebase/auth';
import type { User } from 'firebase/auth';
import { auth, googleProvider } from './firebase';
import { AuthContext } from './authContext';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!!auth);
  const [googleAccessToken, setGoogleAccessToken] = useState<string | null>(null);

  useEffect(() => {
    if (!auth) return;
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u);
      if (!u) setGoogleAccessToken(null);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signInWithGoogle = async () => {
    console.log('[Auth] signInWithGoogle called, auth:', !!auth, 'googleProvider:', !!googleProvider);
    if (!auth || !googleProvider) {
      console.error('Firebase is not initialized. Check that VITE_FIREBASE_* env vars are set and restart the dev server.');
      alert('Firebase is not configured. Make sure your .env file has all VITE_FIREBASE_* variables and restart the dev server.');
      return;
    }
    const result = await signInWithPopup(auth, googleProvider);
    const credential = GoogleAuthProvider.credentialFromResult(result);
    if (credential?.accessToken) {
      setGoogleAccessToken(credential.accessToken);
    }
    const u = result.user;
    try {
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      await fetch(`${apiBase}/api/users/signin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uid: u.uid,
          email: u.email,
          display_name: u.displayName,
          photo_url: u.photoURL,
        }),
      });
    } catch {
      // Backend may not be running — sign-in still works
    }
  };

  const logout = async () => {
    if (!auth) return;
    await signOut(auth);
    setGoogleAccessToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, googleAccessToken, signInWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

import { initializeApp, type FirebaseApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, signInWithPopup } from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

let app: FirebaseApp | null = null

if (firebaseConfig.apiKey && firebaseConfig.appId && firebaseConfig.projectId) {
  try {
    app = initializeApp(firebaseConfig)
  } catch {
    app = null
  }
}

export function isFirebaseConfigured(): boolean {
  return app !== null
}

export async function signInWithGoogle(): Promise<string> {
  if (!app) {
    throw new Error('Google sign-in is not configured on this deployment')
  }
  const auth = getAuth(app)
  const provider = new GoogleAuthProvider()
  const credential = await signInWithPopup(auth, provider)
  return credential.user.getIdToken()
}

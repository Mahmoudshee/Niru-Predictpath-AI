import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Firebase configuration - these are safe to expose (public config)
// You'll need to replace these with your own Firebase project credentials
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyBi1taVzixduzy6ya4eyJViUqtRs2jw8js",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "predictpath.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "predictpath",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "predictpath.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "998560071326",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:998560071326:web:d24d4c7c5d8d092d9cc58f",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication
export const auth = getAuth(app);

// Google Auth Provider
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: "select_account",
});

export default app;

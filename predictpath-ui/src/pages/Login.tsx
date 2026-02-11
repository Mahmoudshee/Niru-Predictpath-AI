
import { useState } from "react";
import { signInWithPopup, signInWithEmailAndPassword } from "firebase/auth";
import { auth, googleProvider } from "@/lib/firebase";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Lock, Mail, Chrome, AlertCircle, ArrowRight } from "lucide-react";

const Login = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleGoogleLogin = async () => {
        setLoading(true);
        setError(null);
        try {
            await signInWithPopup(auth, googleProvider);
            navigate("/");
        } catch (err: any) {
            console.error("Login Error:", err);
            console.error("Error Code:", err.code);
            console.error("Error Message:", err.message);

            if (err.code === 'auth/configuration-not-found') {
                setError("Google Sign-In is not enabled in Firebase Console.");
            } else if (err.code === 'auth/unauthorized-domain') {
                setError("This domain (localhost) is not authorized in Firebase Console.");
            } else if (err.code === 'auth/popup-closed-by-user') {
                setError("Sign-in cancelled.");
            } else {
                setError(err.message || "Failed to sign in with Google");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleEmailLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await signInWithEmailAndPassword(auth, email, password);
            navigate("/");
        } catch (err: any) {
            setError("Invalid email or password");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-background overflow-hidden relative">
            <div className="fixed inset-0 cyber-grid opacity-20 pointer-events-none" />
            <div className="fixed inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none" />

            {/* Background Orbs */}
            <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px]" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-accent/10 rounded-full blur-[100px]" />

            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="relative z-10 w-full max-w-md p-8"
            >
                <div className="bg-card/40 backdrop-blur-xl border border-primary/20 rounded-2xl p-8 shadow-2xl relative overflow-hidden group">
                    {/* Scanning Line Effect */}
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent animate-scan opacity-50" />

                    <div className="flex flex-col items-center mb-8">
                        <div className="relative mb-4">
                            <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse-glow" />
                            <Shield className="w-16 h-16 text-primary relative z-10" strokeWidth={1.5} />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tighter text-glow-primary">
                            PredictPath AI
                        </h1>
                        <p className="text-muted-foreground mt-2 text-sm text-center">
                            Secure Access Intelligence Dashboard
                        </p>
                    </div>

                    {error && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            className="mb-6 p-3 bg-destructive/10 border border-destructive/30 rounded-lg flex items-center gap-3 text-destructive text-sm"
                        >
                            <AlertCircle size={16} />
                            {error}
                        </motion.div>
                    )}

                    <div className="space-y-4">
                        <button
                            onClick={handleGoogleLogin}
                            disabled={loading}
                            className="w-full h-12 flex items-center justify-center gap-3 bg-secondary/50 hover:bg-secondary/80 border border-border hover:border-primary/50 text-foreground transition-all duration-300 rounded-lg group/btn"
                            type="button"
                        >
                            <Chrome className="w-5 h-5 group-hover/btn:text-primary transition-colors" />
                            <span className="font-medium">Sign in with Google</span>
                        </button>

                        <div className="relative my-6">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-border" />
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-background/0 backdrop-blur-sm px-2 text-muted-foreground">Or verify identity</span>
                            </div>
                        </div>

                        <form onSubmit={handleEmailLogin} className="space-y-4">
                            <div className="group/input">
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-5 w-5 text-muted-foreground group-focus-within/input:text-primary transition-colors" />
                                    <input
                                        type="email"
                                        placeholder="Security ID (Email)"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full h-11 pl-10 pr-3 bg-background/50 border border-border rounded-lg focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-muted-foreground/50 text-sm"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="group/input">
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-5 w-5 text-muted-foreground group-focus-within/input:text-primary transition-colors" />
                                    <input
                                        type="password"
                                        placeholder="Access Key (Password)"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full h-11 pl-10 pr-3 bg-background/50 border border-border rounded-lg focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-muted-foreground/50 text-sm"
                                        required
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] transition-all duration-300 flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                                ) : (
                                    <>
                                        Initialize Session <ArrowRight size={18} />
                                    </>
                                )}
                            </button>
                        </form>
                    </div>

                    <div className="mt-6 text-center text-xs text-muted-foreground/60">
                        <p>Protected by End-to-End Enterprise Encryption</p>
                        <p className="font-mono mt-1">v1.2.0-SECURE</p>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;

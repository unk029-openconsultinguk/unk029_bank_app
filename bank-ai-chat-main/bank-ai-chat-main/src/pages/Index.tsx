import { useState, useEffect } from "react";
import { LoginForm } from "@/components/LoginForm";
import { ChatInterface } from "@/components/ChatInterface";

const Index = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = (token: string) => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setIsAuthenticated(false);
  };

  return isAuthenticated ? (
    <ChatInterface onLogout={handleLogout} />
  ) : (
    <LoginForm onLogin={handleLogin} />
  );
};

export default Index;

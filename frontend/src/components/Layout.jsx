import { Outlet } from "react-router-dom";
import ChatWidget from "./ChatWidget";
import Footer from "./Footer";
import Navbar from "./Navbar";

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex-1">
        <Outlet />
      </div>
      <Footer />
      <ChatWidget />
    </div>
  );
}

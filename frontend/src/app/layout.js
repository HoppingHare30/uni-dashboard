import "./globals.css";

export const metadata = {
  title: "Unified Campus Intelligence Dashboard",
  description: "A single, AI-powered space for students to view library books, cafeteria menus, campus events, and academic textbooks.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}

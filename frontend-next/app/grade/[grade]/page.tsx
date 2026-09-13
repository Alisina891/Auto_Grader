export default function GradePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        textAlign: "center",
        background: "linear-gradient(135deg, #0f172a, #1e3a5f)",
        color: "white",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "600px",
          padding: "50px 30px",
          borderRadius: "20px",
          background: "rgba(255, 255, 255, 0.08)",
          backdropFilter: "blur(10px)",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.3)",
        }}
      >
        <div style={{ fontSize: "60px", marginBottom: "20px" }}>
          🔒
        </div>

        <h1 style={{ fontSize: "36px", marginBottom: "15px" }}>
          سایت به‌صورت موقت بسته است
        </h1>

        <p
          style={{
            fontSize: "18px",
            lineHeight: "1.8",
            color: "#dbeafe",
          }}
        >
          این سایت در حال حاضر به‌صورت موقت در دسترس نیست.
          <br />
          ما در حال انجام برخی به‌روزرسانی‌ها و بهبودها هستیم.
        </p>

        <p
          style={{
            marginTop: "25px",
            fontSize: "16px",
            color: "#bfdbfe",
          }}
        >
          لطفاً بعداً دوباره مراجعه کنید.
        </p>

        <div
          style={{
            marginTop: "30px",
            fontSize: "14px",
            color: "#93c5fd",
          }}
        >
          Flying Wings • Auto Grader
        </div>
      </div>
    </main>
  );
}
const goldPrice = document.getElementById("gold-price");
const goldUpdated = document.getElementById("gold-updated");

const formatPrice = (value) => {
    if (typeof value !== "number") {
        return "--";
    }
    return new Intl.NumberFormat("tr-TR", {
        style: "currency",
        currency: "TRY",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
};

const updateGold = async () => {
    try {
        const response = await fetch("/api/gold", { cache: "no-store" });
        const data = await response.json();
        if (!response.ok || data.status !== "ok") {
            throw new Error(data.message || "API hatasi");
        }
        goldPrice.textContent = formatPrice(data.gram_price);
        goldUpdated.textContent = `Son guncelleme: ${data.updated_at || "bilinmiyor"}`;
    } catch (error) {
        goldUpdated.textContent = "Fiyat alinamadi, tekrar denenecek.";
    }
};

updateGold();
setInterval(updateGold, 5000);

class BeautyStoreAnalytics {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.events = [];
        this.startTime = Date.now();
        this.isSending = false; // Cờ ngăn gửi trùng lặp
        
        // Initialize tracking
        this.init();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    getUserId() {
        let userId = localStorage.getItem('beauty_store_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('beauty_store_user_id', userId);
        }
        return userId;
    }

    init() {
        this.trackPageLoad();
        this.setupEventListeners();
        this.trackUserAgent();
        this.trackScreenResolution();

        // Gửi định kỳ các sự kiện còn sót lại (tùy chọn)
        setInterval(() => {
            this.sendTrackingData();
        }, 10000);
    }

    trackPageLoad() {
        const event = {
            eventType: 'page_load',
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            data: {
                url: window.location.href,
                referrer: document.referrer,
                loadTime: Date.now() - this.startTime,
                page: 'home'
            }
        };
        
        this.addEvent(event);
        console.log('📊 Page Load Tracked:', JSON.parse(JSON.stringify(event)));
    }

    trackUserAgent() {
        const event = {
            eventType: 'device_info',
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            data: {
                userAgent: navigator.userAgent,
                language: navigator.language,
                platform: navigator.platform,
                cookieEnabled: navigator.cookieEnabled,
                onlineStatus: navigator.onLine
            }
        };
        
        this.addEvent(event);
    }

    trackScreenResolution() {
        const event = {
            eventType: 'screen_info',
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            data: {
                screenWidth: screen.width,
                screenHeight: screen.height,
                windowWidth: window.innerWidth,
                windowHeight: window.innerHeight,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth
            }
        };
        
        this.addEvent(event);
    }

    trackProductClick(productName, productBrand, productPrice, productEmoji) {
        const event = {
            eventType: 'product_click',
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            data: {
                productName: productName,
                productBrand: productBrand,
                productPrice: productPrice,
                productEmoji: productEmoji,
                timeOnPage: Date.now() - this.startTime
            }
        };
        
        this.addEvent(event);
        console.log('🖱️ Product Click Tracked:', JSON.parse(JSON.stringify(event)));
    }

    trackAddToCart(productName, productBrand, productPrice, productEmoji, quantity = 1) {
        const event = {
            eventType: 'add_to_cart',
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            data: {
                productName: productName,
                productBrand: productBrand,
                productPrice: productPrice,
                productEmoji: productEmoji,
                quantity: quantity,
                totalValue: productPrice * quantity,
                timeOnPage: Date.now() - this.startTime
            }
        };
        
        this.addEvent(event);
        console.log('🛒 Add to Cart Tracked:', JSON.parse(JSON.stringify(event)));
    }

    trackProductDetailView(productName, productBrand, productPrice, productEmoji) {
        const event = {
            eventType: 'product_detail_view',
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            data: {
                productName: productName,
                productBrand: productBrand,
                productPrice: productPrice,
                productEmoji: productEmoji,
                timeOnPage: Date.now() - this.startTime
            }
        };
        
        this.addEvent(event);
        console.log('👁️ Product Detail View Tracked:', JSON.parse(JSON.stringify(event)));
    }

    trackCheckout(cartItems, totalAmount) {
        const event = {
            eventType: 'checkout_attempt',
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            userId: this.userId,
            data: {
                cartItems: cartItems,
                totalAmount: totalAmount,
                itemCount: cartItems.length,
                totalQuantity: cartItems.reduce((sum, item) => sum + item.quantity, 0),
                timeOnPage: Date.now() - this.startTime
            }
        };
        
        this.addEvent(event);
        console.log('💳 Checkout Tracked:', JSON.parse(JSON.stringify(event)));
    }

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            console.log('Click detected:', e.target);
            this.lastClickEvent = e;
        });

        let timeSpent = 0;
        setInterval(() => {
            timeSpent += 1;
            this.timeSpent = timeSpent;
        }, 1000);
    }

    addEvent(event) {
        this.events.push(event);
        if (this.events.length > 100) {
            this.events = this.events.slice(-100);
        }
        // Gửi dữ liệu ngay sau khi thêm sự kiện
        this.sendTrackingData();
    }

    sendTrackingData() {
        if (this.events.length === 0 || this.isSending) return;

        this.isSending = true;
        const trackingData = {
            sessionId: this.sessionId,
            userId: this.userId,
            events: [...this.events],
            sessionInfo: {
                startTime: this.startTime,
                currentTime: Date.now(),
                timeSpent: this.timeSpent || 0
            }
        };

        console.log(`📤 Sending tracking data [${Date.now()}]:`, JSON.parse(JSON.stringify(trackingData)));
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // Timeout sau 5s

        fetch('http://localhost:8000/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(trackingData),
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`Tracking failed: ${response.status}`);
            }
            console.log('Event tracked:', JSON.parse(JSON.stringify(trackingData)));
            this.events = []; // Xóa sau khi gửi thành công
            return response.json();
        })
        .catch(error => {
            console.error('Tracking error:', error, JSON.parse(JSON.stringify(trackingData)));
            // Lưu vào localStorage để retry sau
            localStorage.setItem('pendingTrackingData', JSON.stringify(trackingData));
        })
        .finally(() => {
            this.isSending = false;
        });
    }
}

// Initialize analytics
const analytics = new BeautyStoreAnalytics();

// Export functions
window.trackProductClick = function(productName, productBrand, productPrice, productEmoji) {
    analytics.trackProductClick(productName, productBrand, productPrice, productEmoji);
};

window.trackAddToCart = function(productName, productBrand, productPrice, productEmoji, quantity) {
    analytics.trackAddToCart(productName, productBrand, productPrice, productEmoji, quantity);
};

window.trackProductDetailView = function(productName, productBrand, productPrice, productEmoji) {
    analytics.trackProductDetailView(productName, productBrand, productPrice, productEmoji);
};

window.trackCheckout = function(cartItems, totalAmount) {
    analytics.trackCheckout(cartItems, totalAmount);
};
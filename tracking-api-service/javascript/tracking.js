class BeautyStoreAnalytics {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.events = [];
        this.startTime = Date.now();
        
        // Initialize tracking
        this.init();
    }

    // Generate unique session ID
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Get or create user ID (stored in localStorage for returning users)
    getUserId() {
        let userId = localStorage.getItem('beauty_store_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('beauty_store_user_id', userId);
        }
        return userId;
    }

    // Initialize tracking
    init() {
    }

    // Track page load
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
                page: 'home' // Default page
            }
        };
        
        this.addEvent(event);
        console.log('📊 Page Load Tracked:', event);
    }

    // Track user agent and device info
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

    // Track screen resolution
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

    // Track product click
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
                clickPosition: this.getClickPosition(),
                timeOnPage: Date.now() - this.startTime
            }
        };
        
        this.addEvent(event);
        console.log('🖱️ Product Click Tracked:', event);
    }

    // Track add to cart
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
    console.log('🛒 Add to Cart Tracked:', event);
    // Gọi sendTrackingData ở đây
    this.sendTrackingData()
}

    // Track product detail view
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
        console.log('👁️ Product Detail View Tracked:', event);
    }

    // Track checkout attempt
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
        console.log('💳 Checkout Tracked:', event);
        // Gọi sendTrackingData ở đây
        this.sendTrackingData()
    }

    // Setup event listeners
    setupEventListeners() {
        // Track all clicks
        document.addEventListener('click', (e) => {
            this.lastClickEvent = e;
        });

        // Track time spent on page
        let timeSpent = 0;
        setInterval(() => {
            timeSpent += 1;
            this.timeSpent = timeSpent;
        }, 1000);
    }

    // Add event to queue
    addEvent(event) {
        this.events.push(event);
        
        // Keep only last 100 events to prevent memory issues
        if (this.events.length > 100) {
            this.events = this.events.slice(-100);
        }
    }

    // Send tracking data to server
    sendTrackingData() {
        if (this.events.length === 0) return;

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

        // In production, send to your analytics server
        console.log('📤 Sending tracking data:', trackingData);
        
        // Gửi yêu cầu POST đến API endpoint
        fetch('http://localhost:8000/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(trackingData)
        })
        .then(response => {
            if (!response.ok) {
                console.error('Tracking failed:', response.status);
            } else {
                console.log('Event tracked:', trackingData);
            }
            this.events = [];
        })
        .catch(error => console.error('Tracking error:', trackingData));
    }
}

// Initialize analytics
const analytics = new BeautyStoreAnalytics();

// Export functions for use in main HTML file
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
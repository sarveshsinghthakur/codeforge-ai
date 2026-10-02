import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../lib/api';
import { useAuth } from '../App';
import { useToast } from '../components/Toast';

interface Plan {
  id: string;
  name: string;
  interval: string;
  price_usd: number;
  price_inr: number;
  description: string;
  features: string[];
  popular: boolean;
}

interface SubStatus {
  active: boolean;
  plan?: string | null;
  provider?: string | null;
  status?: string | null;
  amount?: number | null;
  currency?: string | null;
  expires_at?: string | null;
  days_left?: number | null;
  is_admin?: boolean;
}

type Provider = 'paypal' | 'paytm';

export default function Payment() {
  const { token } = useAuth();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [sub, setSub] = useState<SubStatus | null>(null);
  const [selectedPlan, setSelectedPlan] = useState('annual');
  const [provider, setProvider] = useState<Provider>('paypal');
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    api.get('/payments/plans').then(res => setPlans(res.data)).catch(() => {});
    if (token) {
      api.get('/payments/subscription').then(res => setSub(res.data)).catch(() => setSub(null));
    } else {
      setSub(null);
    }
  }, [token]);

  useEffect(() => {
    if (searchParams.get('cancelled')) {
      toast('Payment cancelled — you were not charged', 'info');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const price = (p: Plan) => (provider === 'paypal' ? p.price_usd : p.price_inr);
  const symbol = provider === 'paypal' ? '$' : '₹';
  const plan = plans.find(p => p.id === selectedPlan) || plans[1];
  const yearlyMonthly = plans.find(p => p.id === 'annual');
  const monthly = plans.find(p => p.id === 'monthly');
  const savings = yearlyMonthly && monthly
    ? Math.max(0, Math.round((1 - yearlyMonthly.price_usd / (monthly.price_usd * 12)) * 100))
    : 0;

  const pay = async () => {
    if (!token) {
      toast('Sign in to start your subscription', 'info');
      window.location.href = '/login';
      return;
    }
    if (!plan) return;
    setPaying(true);
    try {
      const res = await api.post('/payments/checkout', {
        plan: plan.id,
        provider,
        origin_url: window.location.origin,
      });
      const data = res.data;

      if (data.demo) {
        // Demo sandbox: no real gateway — verify the order directly.
        window.location.href = `/payment/verify?provider=${data.provider}&order_id=${data.order_id}&demo=1`;
        return;
      }
      const fields = data.form_fields || {};
      if (Object.keys(fields).length > 0) {
        // Paytm hosted checkout: auto-submit the signed form.
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = data.redirect_url;
        for (const [k, v] of Object.entries(fields)) {
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = k;
          input.value = String(v);
          form.appendChild(input);
        }
        document.body.appendChild(form);
        form.submit();
        return;
      }
      window.location.href = data.redirect_url;
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      toast(typeof detail === 'string' ? detail : 'Could not start checkout', 'error');
      setPaying(false);
    }
  };

  if (plans.length === 0) {
    return <div className="page-loading"><div className="loading-spinner" /></div>;
  }

  const active = !!sub?.active;

  return (
    <div className="page-container payment-page">
      <div className="payment-hero">
        <span className="payment-hero-badge">CodeForge Premium</span>
        <h1>{active ? 'Your subscription is active' : 'Unlock every problem'}</h1>
        <p>
          {active
            ? 'Medium and Hard problems are unlocked on your account.'
            : 'Go beyond the basics — unlock all Medium and Hard problems, plus the full AI copilot.'}
        </p>
      </div>

      {active && sub ? (
        <div className="glass-card premium-active-card">
          <div className="premium-check">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div className="premium-active-info">
            <div className="premium-plan-name">
              {sub.plan === 'annual' ? 'Annual' : 'Monthly'} Premium
              <span className="premium-provider-tag">{(sub.provider || '').toUpperCase()}</span>
            </div>
            <div className="premium-active-meta">
              {sub.expires_at && <>Renews / expires <strong>{new Date(sub.expires_at).toLocaleDateString()}</strong></>}
              {sub.days_left != null && <> · <strong>{sub.days_left}</strong> days left</>}
            </div>
            {sub.amount != null && (
              <div className="premium-active-meta">
                Paid {sub.currency === 'INR' ? '₹' : '$'}{sub.amount} via {sub.provider}
              </div>
            )}
          </div>
          <Link to="/problems" className="btn btn-primary">Start solving</Link>
        </div>
      ) : (
        <>
          <div className="plan-grid">
            {plans.map(p => (
              <button
                key={p.id}
                type="button"
                className={`plan-card glass-card ${selectedPlan === p.id ? 'selected' : ''}`}
                onClick={() => setSelectedPlan(p.id)}
              >
                {p.popular && <span className="plan-popular">Best value</span>}
                {p.id === 'annual' && savings > 0 && <span className="plan-save">Save {savings}%</span>}
                <div className="plan-name">{p.name}</div>
                <div className="plan-price">
                  <span className="plan-currency">{symbol}</span>
                  {price(p).toFixed(price(p) % 1 === 0 ? 0 : 2)}
                  <span className="plan-interval">/{p.interval === 'year' ? 'year' : 'month'}</span>
                </div>
                {p.id === 'annual' && (
                  <div className="plan-subprice">
                    {symbol}{(price(p) / 12).toFixed(2)}/mo billed yearly
                  </div>
                )}
                <div className="plan-desc">{p.description}</div>
                <ul className="plan-features">
                  {p.features.map(f => (
                    <li key={f}>
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
                <span className="plan-select-indicator" />
              </button>
            ))}
          </div>

          <div className="payment-checkout glass-card">
            <div className="provider-row">
              <span className="provider-label">Pay with</span>
              <div className="provider-toggle">
                <button
                  type="button"
                  className={`provider-btn ${provider === 'paypal' ? 'active' : ''}`}
                  onClick={() => setProvider('paypal')}
                >
                  <span className="provider-logo paypal-logo">Pay</span>Pal
                </button>
                <button
                  type="button"
                  className={`provider-btn ${provider === 'paytm' ? 'active' : ''}`}
                  onClick={() => setProvider('paytm')}
                >
                  Pay<span className="provider-logo paytm-logo">tm</span>
                </button>
              </div>
            </div>

            <div className="checkout-summary">
              <div className="checkout-line">
                <span>CodeForge Premium — {plan?.name} plan</span>
                <strong>{symbol}{plan ? price(plan).toFixed(price(plan) % 1 === 0 ? 0 : 2) : ''}</strong>
              </div>
              <div className="checkout-line muted">
                <span>Billing</span>
                <span>{provider === 'paypal' ? 'USD via PayPal' : 'INR via Paytm'}</span>
              </div>
            </div>

            <button className="btn btn-primary pay-btn" onClick={pay} disabled={paying}>
              {paying
                ? 'Redirecting…'
                : `Subscribe for ${symbol}${plan ? price(plan).toFixed(price(plan) % 1 === 0 ? 0 : 2) : ''} / ${plan?.interval === 'year' ? 'year' : 'month'}`}
            </button>
            <div className="pay-trust">
              <span>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                Secure checkout
              </span>
              <span>Cancel anytime</span>
              <span>Instant unlock after verification</span>
            </div>
          </div>

          <div className="payment-faq">
            <div className="faq-item">
              <strong>What do I unlock?</strong>
              <p>All Medium and Hard problems become available — descriptions, starter templates, test runs and submissions.</p>
            </div>
            <div className="faq-item">
              <strong>How does verification work?</strong>
              <p>After checkout you are redirected to a verification page. Once the payment is confirmed, your account is upgraded immediately.</p>
            </div>
            <div className="faq-item">
              <strong>Which payment methods are supported?</strong>
              <p>PayPal (international cards & wallet) and Paytm (UPI, wallet & cards).</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../lib/api';

interface SubStatus {
  active: boolean;
  plan?: string | null;
  provider?: string | null;
  expires_at?: string | null;
  days_left?: number | null;
}

type State = 'verifying' | 'success' | 'failed';

export default function PaymentVerify() {
  const [searchParams] = useSearchParams();
  const [state, setState] = useState<State>('verifying');
  const [status, setStatus] = useState<SubStatus | null>(null);
  const [error, setError] = useState<string>('');
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const provider = searchParams.get('provider');
    const orderId = searchParams.get('order_id') || searchParams.get('token');
    const cancelled = searchParams.get('cancelled');

    if (cancelled) {
      setError('Payment was cancelled before completion.');
      setState('failed');
      return;
    }
    if (!provider || !orderId) {
      setError('Missing payment reference — start again from the billing page.');
      setState('failed');
      return;
    }

    const params: Record<string, string> = {};
    searchParams.forEach((value, key) => {
      if (!['provider', 'order_id', 'token', 'demo', 'cancelled'].includes(key)) {
        params[key] = value;
      }
    });

    api.post('/payments/verify', { provider, order_id: orderId, params })
      .then(res => {
        setStatus(res.data);
        setState(res.data.active ? 'success' : 'failed');
        if (!res.data.active) setError('The payment could not be confirmed.');
      })
      .catch((err: any) => {
        const detail = err.response?.data?.detail;
        if (detail && typeof detail === 'object') {
          setError(detail.message || detail.code || 'Payment verification failed.');
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Payment verification failed. Please contact support.');
        }
        setState('failed');
      });
  }, [searchParams]);

  return (
    <div className="page-container verify-page">
      <div className="glass-card verify-card">
        {state === 'verifying' && (
          <>
            <div className="loading-spinner verify-spinner" />
            <h1>Verifying your payment…</h1>
            <p>Hang tight — we are confirming the transaction with the payment provider.</p>
          </>
        )}

        {state === 'success' && (
          <>
            <div className="verify-icon success">
              <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h1>Payment verified!</h1>
            <p className="verify-sub">
              Your <strong>{status?.plan === 'annual' ? 'Annual' : 'Monthly'}</strong> Premium
              subscription is active.
            </p>
            <div className="verify-unlock-note">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 9.9-1" />
              </svg>
              Medium and Hard problems are now unlocked on your account.
            </div>
            {status?.expires_at && (
              <p className="verify-expiry">
                Valid until {new Date(status.expires_at).toLocaleDateString()}
                {status.days_left != null && <> · {status.days_left} days left</>}
              </p>
            )}
            <div className="verify-actions">
              <Link to="/problems" className="btn btn-primary">Browse all problems</Link>
              <Link to="/payment" className="btn btn-secondary">Billing details</Link>
            </div>
          </>
        )}

        {state === 'failed' && (
          <>
            <div className="verify-icon failed">
              <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </div>
            <h1>Payment not completed</h1>
            <p className="verify-sub">{error}</p>
            <div className="verify-actions">
              <Link to="/payment" className="btn btn-primary">Try again</Link>
              <Link to="/problems" className="btn btn-secondary">Back to problems</Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

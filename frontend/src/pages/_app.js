import '@/styles/globals.css';

/**
 * WebGuard AI — App Wrapper
 * يُغلّف جميع الصفحات بالإعدادات العامة.
 */
export default function App({ Component, pageProps }) {
  return <Component {...pageProps} />;
}

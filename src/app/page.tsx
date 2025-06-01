'use client';

import { BillSearch } from '@/components/bill-search';
import { useState } from 'react';

export default function Home() {
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [error, setError] = useState('');

  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(event.target.value);
  };

  const handleLogin = () => {
    if (password === 'sc151202') {
      setIsLoggedIn(true);
      setError('');
    } else {
      setError('Incorrect password');
    }
  };

  // You could potentially fetch initial bills server-side here if needed
  // const initialBills = await fetchInitialBills();
  return !isLoggedIn ? (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black">
      <div className="bg-white p-8 rounded-lg shadow-md w-96 border border-gray-300">
        <h2 className="text-3xl font-bold mb-8 text-center text-gray-800">Login</h2>
        <div className="mb-4">
          <label className="block text-gray-700 text-lg font-medium mb-2" htmlFor="password">
            Password
          </label>
          <input
            className="shadow appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline border-gray-400"
            id="password"
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={handlePasswordChange}
          />
        </div>        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        <button
          className="bg-gray-800 hover:bg-gray-900 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline w-full transition duration-300"
          onClick={handleLogin}
        >
          Enter
        </button>
      </div>
    </div>
  ) : (
    <main className="min-h-screen bg-background"> <BillSearch /> </main>
  )
}

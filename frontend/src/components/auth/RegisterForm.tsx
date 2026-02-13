import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { registerSchema } from '../../schemas/auth';
import type { RegisterFormData } from '../../schemas/auth';
import { useAuth } from '../../context/AuthContext';

const RegisterForm: React.FC = () => {
  const navigate = useNavigate();
  const { register: registerUser, isLoading, error, clearError } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      clearError();
      await registerUser(data);
      navigate('/decks');
    } catch (error) {
      // Error is handled by the auth context
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="bg-gray-800 rounded-xl shadow-lg p-8 max-w-md w-full mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-yellow-500 mb-2">
            Create Account
          </h1>
          <p className="text-gray-400">
            Join MTG Commander to manage your decks
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900 bg-opacity-50 border border-red-500 rounded-lg">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-100 mb-2">
              Username
            </label>
            <input
              {...register('username')}
              type="text"
              id="username"
              className="bg-gray-800 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
              placeholder="username"
              disabled={isLoading}
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-400">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-100 mb-2">
              Email Address
            </label>
            <input
              {...register('email')}
              type="email"
              id="email"
              className="bg-gray-800 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
              placeholder="your@email.com"
              disabled={isLoading}
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-100 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                id="password"
                className="bg-gray-800 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full pr-10"
                placeholder="••••••••"
                disabled={isLoading}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
          
          </div>

          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-100 mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <input
                {...register('confirm_password')}
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirm_password"
                className="bg-gray-800 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full pr-10"
                placeholder="••••••••"
                disabled={isLoading}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            {errors.confirm_password && (
              <p className="mt-1 text-sm text-red-400">{errors.confirm_password.message}</p>
            )}
          </div>

          <div className="flex items-center">
            <input
              id="terms"
              name="terms"
              type="checkbox"
              className="h-4 w-4 text-yellow-500 focus:ring-yellow-500 border-gray-600 rounded"
              required
            />
            <label htmlFor="terms" className="ml-2 block text-sm text-gray-300">
              I agree to the{' '}
              <Link to="/terms" className="text-yellow-500 hover:text-yellow-400">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link to="/privacy" className="text-yellow-500 hover:text-yellow-400">
                Privacy Policy
              </Link>
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="bg-yellow-500 text-gray-900 font-semibold py-2 px-4 rounded-lg hover:bg-yellow-400 transition-colors duration-200 w-full flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-gray-400">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-medium text-yellow-500 hover:text-yellow-400"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterForm;

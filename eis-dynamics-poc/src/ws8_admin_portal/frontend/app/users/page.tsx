'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit, Trash2, X, User as UserIcon, Shield } from 'lucide-react';
import { usersApi } from '@/lib/api';
import { formatDateTime, getRoleLabel } from '@/lib/utils';
import type { User, UserRole } from '@/lib/types';

const roleOptions: { value: UserRole; label: string }[] = [
  { value: 'admin', label: 'Administrator' },
  { value: 'approver', label: 'Approver' },
  { value: 'config_manager', label: 'Config Manager' },
  { value: 'viewer', label: 'Viewer' },
  { value: 'cost_analyst', label: 'Cost Analyst' },
];

function UserRow({
  user,
  onEdit,
  onDelete,
}: {
  user: User;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
}) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-6 py-4">
        <div className="flex items-center">
          <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
            <span className="text-primary-600 font-medium">
              {user.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="ml-3">
            <p className="font-medium text-slate-900">{user.name}</p>
            <p className="text-sm text-slate-500">{user.email}</p>
          </div>
        </div>
      </td>
      <td className="px-6 py-4">
        <span className="badge-primary">{getRoleLabel(user.role)}</span>
      </td>
      <td className="px-6 py-4">
        {user.is_active ? (
          <span className="badge-success">Active</span>
        ) : (
          <span className="badge-gray">Inactive</span>
        )}
      </td>
      <td className="px-6 py-4 text-sm text-slate-500">
        {user.last_login ? formatDateTime(user.last_login) : 'Never'}
      </td>
      <td className="px-6 py-4 text-sm text-slate-500">
        {formatDateTime(user.created_at)}
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center space-x-2">
          <button onClick={() => onEdit(user)} className="btn-ghost p-2">
            <Edit className="w-4 h-4" />
          </button>
          <button onClick={() => onDelete(user)} className="btn-ghost p-2 text-danger-600">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  );
}

function UserModal({
  user,
  onClose,
  onSave,
  isSaving,
}: {
  user: User | null;
  onClose: () => void;
  onSave: (data: any) => void;
  isSaving: boolean;
}) {
  const [formData, setFormData] = useState({
    email: user?.email || '',
    name: user?.name || '',
    role: user?.role || 'viewer',
    password: '',
    is_active: user?.is_active ?? true,
  });

  const isEdit = !!user;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = { ...formData };
    if (!data.password) delete (data as any).password;
    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">
            {isEdit ? 'Edit User' : 'Create User'}
          </h3>
          <button onClick={onClose} className="btn-ghost p-2">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Email *</label>
            <input
              type="email"
              className="input"
              value={formData.email}
              onChange={(e) => setFormData((f) => ({ ...f, email: e.target.value }))}
              required
              disabled={isEdit}
            />
          </div>
          <div>
            <label className="label">Name *</label>
            <input
              type="text"
              className="input"
              value={formData.name}
              onChange={(e) => setFormData((f) => ({ ...f, name: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="label">Role *</label>
            <select
              className="select"
              value={formData.role}
              onChange={(e) => setFormData((f) => ({ ...f, role: e.target.value as UserRole }))}
            >
              {roleOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">
              Password {isEdit ? '(leave blank to keep current)' : '*'}
            </label>
            <input
              type="password"
              className="input"
              value={formData.password}
              onChange={(e) => setFormData((f) => ({ ...f, password: e.target.value }))}
              required={!isEdit}
              minLength={8}
            />
          </div>
          {isEdit && (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData((f) => ({ ...f, is_active: e.target.checked }))}
                className="rounded border-slate-300"
              />
              <label htmlFor="is_active" className="text-sm text-slate-700">
                Active
              </label>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={isSaving} className="btn-primary">
              {isSaving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [roleFilter, setRoleFilter] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['users', roleFilter],
    queryFn: () => usersApi.list({ role: roleFilter || undefined }),
  });

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => usersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setEditUser(null);
      setShowModal(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const handleEdit = (user: User) => {
    setEditUser(user);
    setShowModal(true);
  };

  const handleDelete = (user: User) => {
    if (confirm(`Are you sure you want to deactivate ${user.name}?`)) {
      deleteMutation.mutate(user.id);
    }
  };

  const handleSave = (formData: any) => {
    if (editUser) {
      updateMutation.mutate({ id: editUser.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditUser(null);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
          <p className="text-slate-500">Manage admin portal users and roles</p>
        </div>
        <button
          onClick={() => {
            setEditUser(null);
            setShowModal(true);
          }}
          className="btn-primary flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add User
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-body flex items-center">
            <div className="p-3 bg-primary-100 rounded-lg mr-4">
              <UserIcon className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Total Users</p>
              <p className="text-2xl font-bold text-slate-900">{data?.total || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-body flex items-center">
            <div className="p-3 bg-success-50 rounded-lg mr-4">
              <Shield className="w-6 h-6 text-success-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Admins</p>
              <p className="text-2xl font-bold text-slate-900">
                {data?.users?.filter((u: User) => u.role === 'admin').length || 0}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Active</p>
            <p className="text-2xl font-bold text-success-600">
              {data?.users?.filter((u: User) => u.is_active).length || 0}
            </p>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <p className="text-sm text-slate-500">Inactive</p>
            <p className="text-2xl font-bold text-slate-400">
              {data?.users?.filter((u: User) => !u.is_active).length || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center space-x-4">
        <select
          className="select w-48"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
        >
          <option value="">All Roles</option>
          {roleOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <span className="text-sm text-slate-500">
          Showing {data?.users?.length || 0} of {data?.total || 0} users
        </span>
      </div>

      {/* Table */}
      <div className="card">
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Last Login</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data?.users?.map((user: User) => (
                  <UserRow
                    key={user.id}
                    user={user}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <UserModal
          user={editUser}
          onClose={handleCloseModal}
          onSave={handleSave}
          isSaving={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}

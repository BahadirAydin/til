---
title: "Condition variables can wake up spuriously"
date: 2026-10-11
draft: false
---

Here's something interesting: a thread blocked on a condition variable can wake up even if nobody notified it.

```cpp
std::unique_lock lock(m);
cv.wait(lock);  // can return without any notify_one or notify_all
```

This is called a spurious wakeup and it's not a bug in your libc. The C++ standard says `wait` unblocks when notified
"or spuriously", and POSIX says the same for `pthread_cond_wait`.

Why would anyone allow that? Getting exactly one thread to wake up for exactly one notify needs extra synchronization
inside every wait and notify, and on a multiprocessor that gets expensive. The POSIX rationale mentions implementations
where signaling the condition from different CPUs at the same time can wake more than one waiter. Letting that happen
keeps them simpler and faster.

Signals can do it too. If a signal arrives while a thread is blocked in `pthread_cond_wait`, POSIX lets the wait either
go back to sleep after the handler or just return 0.

And allowing it costs almost nothing, because a woken thread has to check its condition again anyway. Waking up and
getting the mutex back are separate steps, so another thread can get the lock first and change the state. Even after a
real notify the thing you waited for might already be gone.

So when `wait` returns don't assume what you waited for actually happened. Check again. The predicate overload does that
loop for you:

```cpp
cv.wait(lock, [&] { return ready; });  // same as while (!ready) cv.wait(lock);
```

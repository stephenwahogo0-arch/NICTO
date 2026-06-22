"""Run KYROS test suite and print summary."""
import sys, asyncio, time
sys.path.insert(0, "packages/kyros-core/src")
import test_nikto

start = time.time()
success = asyncio.run(test_nikto.main())
elapsed = time.time() - start
print(f"\n  Completed in {elapsed:.1f}s")
print(f"  Result: {'ALL PASSED' if success else 'SOME FAILED'}")
sys.exit(0 if success else 1)

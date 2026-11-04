// The same Person message as bench/main.mettle, through C++ protobuf.
// Build steps: docs/testing.md.
#include <chrono>
#include <cstdio>
#include <string>
#include "basic.pb.h"
using namespace std::chrono;
int main() {
  demo::v1::Person p;
  p.set_name("Ada Lovelace"); p.set_id(1815); p.set_email("ada@analytical.engine");
  for (int i = 0; i < 4; i++) { auto* ph = p.add_phones(); ph->set_number("+44 20 7946 0000"); ph->set_type(demo::v1::Person::HOME); }
  for (int i = 0; i < 16; i++) p.add_scores(i * 1000);
  p.add_tags("mathematician"); p.add_tags("writer");
  p.set_height(1.65); p.set_balance(-123456); p.set_active(true);
  std::string out; p.SerializeToString(&out);
  const int n = 200000; size_t sz = out.size();
  auto t0 = steady_clock::now();
  for (int i = 0; i < n; i++) { out.clear(); p.SerializeToString(&out); }
  auto t1 = steady_clock::now();
  double ns = duration_cast<nanoseconds>(t1 - t0).count() / (double)n;
  printf("C++ protobuf encode (%zu B): %.0f MB/s, %.0f ns per message\n", sz, sz / ns * 1e9 / 1048576, ns);
  demo::v1::Person q;
  t0 = steady_clock::now();
  for (int i = 0; i < n; i++) { q.Clear(); q.ParseFromString(out); }
  t1 = steady_clock::now();
  ns = duration_cast<nanoseconds>(t1 - t0).count() / (double)n;
  printf("C++ protobuf decode (%zu B): %.0f MB/s, %.0f ns per message\n", sz, sz / ns * 1e9 / 1048576, ns);
}

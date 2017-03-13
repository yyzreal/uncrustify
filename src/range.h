#ifndef __RANGE_H__
#define __RANGE_H__

#include "uncrustify_types.h"
#include <vector>


bool parse_range(const char *str, std::vector<range_t>& ranges);


inline bool range_overlapps_with(const range_t &lhs, const range_t &rhs)
{
   return (lhs.offset + lhs.length > rhs.offset) &&
      (lhs.offset < rhs.offset + rhs.length);
}

inline bool range_contains_range(const range_t &lhs, const range_t &rhs)
{
   return rhs.offset >= lhs.offset &&
      (rhs.offset + rhs.length) <= (lhs.offset + lhs.length);
}

inline bool range_contains_line(const range_t& r, unsigned line)
{
   return r.offset <= line && (r.offset + r.length) >= line;
}

#endif // __RANGE_H__

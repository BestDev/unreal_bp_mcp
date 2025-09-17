// Copyright Epic Games, Inc. All Rights Reserved.
// UnrealBlueprintMCP API definitions

#pragma once

#include "CoreMinimal.h"

// API export/import macros for the UnrealBlueprintMCP module
#ifndef UNREALBLUEPRINTMCP_API
	#ifdef UNREALBLUEPRINTMCP_EXPORTS
		#define UNREALBLUEPRINTMCP_API DLLEXPORT
	#else
		#define UNREALBLUEPRINTMCP_API DLLIMPORT
	#endif
#endif